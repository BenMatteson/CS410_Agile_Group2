import logging

import paramiko
import pysftp
from os.path import expanduser, isfile
from paramiko import ssh_exception


class SFTP(object):
    def __init__(self, hostname, username, password=None, private_key_password=None):
        self.local_directory = expanduser('~')
        self.connection = initiate_connection(hostname, username, password, private_key_password)

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

    def rm(self, args):
        """
            Remove file from remote path given by argument. Arg may include path ('/').
        """
        if len(args) != 1:
            raise TypeError("Usage: rm [filename | path/to/filename]")
        else:
            if self.connection.isfile(args[0]):
                self.connection.remove(args[0])
            else:
                print("Usage: rm [filename | path/to/filename]")

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
