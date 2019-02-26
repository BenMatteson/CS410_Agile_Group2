import logging
import os
import paramiko
import pysftp
import ntpath
from os.path import expanduser, isfile, exists, join
from os import mkdir
from paramiko import ssh_exception

DOWNLOADS_DIRECTORY = "downloads"


class SFTP(object):
    def __init__(self, hostname, username, password=None, private_key_password=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key_password = private_key_password
        self.local_directory = expanduser('~')
        if not exists(DOWNLOADS_DIRECTORY):
            mkdir(DOWNLOADS_DIRECTORY)
        self.connection = self.initiate_connection()

    def is_connected(self):
        """Check the connection (using the listdir() method) to confirm that it's active."""
        return True if self.connection.listdir() else False

    # region Commands Section
    def ping(self):
        return "pong" if self.connection.listdir() else "nothing happened"

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

    def mkdir(self, args):
        """
            Creates directory on remote path passed as an argument. Directories
            are created with permissions 775.
        """
        if len(args) != 1:
            raise TypeError("Usage: mkdir [dirname | path/to/dirname]")
        else:
            if args[0].find('/') != -1:
                self.connection.makedirs(args[0], mode = 775)
            else:
                self.connection.mkdir(args[0], mode = 775)

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

    def lsl(self):
        '''It does list all files and directories in your local machine. It will start with local folder where the
         script exist'''
        currentDirectoryPath = os.getcwd()
        filesInCurrentDirectory = os.listdir(os.getcwd())
        print(currentDirectoryPath)
        for fileName in filesInCurrentDirectory:
            print(fileName)

    def closeAndExit(self):
        try:
            self.connection.close()
            exit()
        except Exception:
            pass

    def initiate_connection(self):
        # Connect, checking hostkey or caching on first connect
        # Based off of this stackoverflow question:
        #     https://stackoverflow.com/questions/53666106/use-paramiko-autoaddpolicy-with-pysftp
    
        # configure pysftp CnOpts
        hostkeys = None
        cnopts = pysftp.CnOpts()  # loads hostkeys from known_hosts.ssh
        if cnopts.hostkeys.lookup(self.hostname) is None:
            logging.debug('Key for host: ' + self.hostname + ' was not found in known_hosts')
            hostkeys = cnopts.hostkeys
            cnopts.hostkeys = None
    
        args = {'host': self.hostname,
                'username': self.username,
                'cnopts': cnopts}
    
        # Determine what type of authentication to use based on parameters provided
        ssh_key = expanduser('~') + '/.ssh/id_rsa'
        if self.password is not None:
            logging.debug('Using plaintext authentication')
            args['password'] = self.password
        elif isfile(ssh_key):
            logging.debug('Got SSH key: ' + ssh_key)
            # the file at ~/.ssh/id_rsa exists - use it as the (default) private key
            args['private_key'] = ssh_key
            if self.private_key_password is not None:
                logging.debug('Using public key authentication with DER-encoded private key')
                args['private_key_pass'] = self.private_key_password
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
            logging.debug('Appending new hostkey for ' + self.hostname + ' to known_hosts, and writing to disk...')
            hostkeys.add(self.hostname, connection.remote_server_key.get_name(),
                         connection.remote_server_key)
            hostkeys.save(pysftp.helpers.known_hosts())
    
        return connection
