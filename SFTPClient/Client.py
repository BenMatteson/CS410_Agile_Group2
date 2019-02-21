import logging

import paramiko
import pysftp
import ntpath
from os.path import expanduser, isfile, exists, join
from os import mkdir
from paramiko import ssh_exception

DOWNLOADS_DIRECTORY = "downloads"

class SFTP(object):
    def __init__(self, hostname, username, password=None, private_key_password=None):
        self.local_directory = expanduser('~')
        self.connection = initiate_connection(hostname, username, password, private_key_password)
        if not exists(DOWNLOADS_DIRECTORY):
            mkdir(DOWNLOADS_DIRECTORY)

    def is_connected(self):
        """Check the connection (using the listdir() method) to confirm that it's active."""
        if self.connection.listdir():
            return True

    # region Commands Section
    def ping(self, _args):
        if self.connection.listdir():
            return 'pong'

    def ls(self, args):
        """List directory contents on the remote server"""
        results = None
        if len(args) is 0:
            results = self.connection.listdir()
        elif len(args) is 1:
            results = self.connection.listdir(args[0])
        else:
            raise TypeError('ls() takes exactly zero or one arguments (' + str(len(args)) + ' given)')
        return results
    
    def chmod(self, args):
        """Change or modify permissions of directories and files on the remote server
        
            Set the mode of a remotepath to mode, where mode is an integer representation
            of the octal mode to use.
        """
        if len(args) is 2:
            self.connection.chmod(args[0], int(args[1]))
        else:
            raise TypeError('chmod() takes exactly two arguments (' + str(len(args)) + ' given)')
    
    def rmdir_r(self, args):
        """
        Recursively delete a directory and all it's files and directories
        """
        if len(args) != 1:
            raise TypeError('rmdir_r() takes exactly one argument (' + str(len(args)) + ' given)')

        if self.connection.isdir(args[0]):
            dirs = []
            self.connection.walktree(args[0], self.connection.remove, dirs.append, self.connection.remove)
            for dir in reversed(dirs):
                self.connection.rmdir(dir)
            self.connection.rmdir(args[0])
        else:
            raise IOError(f"Error: '{args[0]}' is not a directory")
        
    def get(self, args):
        """
        Downloads a remote file to the local machine. Given a single remotepath
        argument (arg[0]), the file is placed in the DOWNLOADS_DIRECTORY. If
        given a remotepath argument (arg[0]) and a localpath argument (arg[1]),
        the file is downloaded to the localpath.
        """
        if len(args) < 1 or len(args) > 2:
            raise TypeError("get() takes 1 or 2 arguments (" + str(len(args)) + " given)")
            
        # Check file exists or pysftp will create an empty file in the target directory
        if self.connection.isfile(args[0]):
            if len(args) is 1:
                head, tail = ntpath.split(args[0])
                remote_file = tail or ntpath.basename(head)
                localpath = join(DOWNLOADS_DIRECTORY, remote_file) 
                self.connection.get(args[0], localpath)
            elif len(args) is 2:
                self.connection.get(args[0], expanduser(args[1]))
        else:
            raise IOError(f"The remote path '{args[0]}' is not a file")

    # endregion

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass


def initiate_connection(hostname, username, password=None, private_key_password=None):
    # Connect, checking hostkey or caching on first connect
    # Based off of this stackoverflow question:
    #     https://stackoverflow.com/questions/53666106/use-paramiko-autoaddpolicy-with-pysftp

    # configure pysftp CnOpts
    hostkeys = None
    cnopts = pysftp.CnOpts()  # loads hostkeys from known_hosts.ssh
    if cnopts.hostkeys.lookup(hostname) is None:
        logging.debug('Key for host: ' + hostname + ' was not found in known_hosts')
        hostkeys = cnopts.hostkeys
        cnopts.hostkeys = None

    args = {'host': hostname,
            'username': username,
            'cnopts': cnopts}

    # Determine what type of authentication to use based on parameters provided
    ssh_key = expanduser('~') + '/.ssh/id_rsa'
    if password is not None:
        logging.debug('Using plaintext authentication')
        args['password'] = password
    elif isfile(ssh_key):
        logging.debug('Got SSH key: ' + ssh_key)
        # the file at ~/.ssh/id_rsa exists - use it as the (default) private key
        args['private_key'] = ssh_key
        if private_key_password is not None:
            logging.debug('Using public key authentication with DER-encoded private key')
            args['private_key_pass'] = private_key_password
        else:
            logging.debug('Using public key authentication with plaintext private key')
    else:
        raise ssh_exception.BadAuthenticationType('No supported authentication methods available',
                                                  ['password', 'public_key'])

    # connect using the authentication type determined above
    logging.debug('Connecting using arguments: ' + str(args))
    try:
        connection = pysftp.Connection(**args)
    except paramiko.SSHException as e:
        logging.critical(e)
        raise

    # On first connect, Save the new hostkey to known_hosts
    if hostkeys is not None:
        logging.debug('Appending new hostkey for ' + hostname + ' to known_hosts, and writing to disk...')
        hostkeys.add(hostname, connection.remote_server_key.get_name(),
                     connection.remote_server_key)
        hostkeys.save(pysftp.helpers.known_hosts())

    return connection
