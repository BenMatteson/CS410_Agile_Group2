#!/usr/local/bin/python3
import argparse
import warnings

import pysftp
import sys
from os.path import expanduser,isfile
from paramiko import ssh_exception

HELP_COMMAND_SPACING = 35  # Max length(+1) of sample commands in help files


def main(argv=None):
    sftp = SFTP(argv)
    sftp.initiate_connection()
    if sftp.connection is not None:
        print("Connection Successful!\n"
              "Type a command or 'help' to see available commands")
    else:
        print("Unable to connect, please check your connection information")
        quit(1)
    while True:
        try:
            command = input('> ')
            sftp.execute_command(command)
        except (ValueError, FileNotFoundError) as e:
            print(e)
            continue


def capture_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Input host name', required=True)
    parser.add_argument('-U', '--username', help='input username', required=True)
    parser.add_argument('-P', '--password', help='input password', required=False)
    parser.add_argument('-p', '--private_key_password', help='Passphrase required to decrypt private key', required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', required=False, action='store_true')
    parser.set_defaults(verbose=None)
    arguments = parser.parse_args()
    return arguments


class SFTP(object):
    def __init__(self, args):
        self.args = vars(args)
        self.verbose = self.args['verbose']
        self.hostName = self.args['host']
        self.userName = self.args['username']
        if 'password' in self.args and self.args['password'] is not None:
            # the user supplied password input
            self.password = self.args['password']
        if 'private_key_password' in self.args and self.args['private_key_password'] is not None:
            # the user supplied private key password input
            self.private_key_password = self.args['private_key_password']
        known_hosts = expanduser('~') + '/.ssh/known_hosts'
        if isfile(known_hosts):
            if self.verbose:
                print('Got known_hosts: ' + known_hosts)
            # the file at ~/.ssh/known_hosts exists - use it as the (default) known_hosts file
            self.known_hosts = known_hosts
        ssh_key = expanduser('~') + '/.ssh/id_rsa'
        if isfile(ssh_key):
            if self.verbose:
                print('Got SSH key: ' + ssh_key)
            # the file at ~/.ssh/id_rsa exists - use it as the (default) private key
            self.private_key = ssh_key
        # configure pysftp CnOpts to use the known_hosts file that was found at the path above
        self.cnopts = pysftp.CnOpts()
        if hasattr(self, 'known_hosts'):
            print("Loading known_hosts")
            self.cnopts.hostkeys.load(self.known_hosts)
        self.connection = None

    def initiate_connection(self):
        """Does initialize connection using  host name, user name & password
        
        This method will attempt to determine whenther it should be using one of the
        following authentication methods (in the order provided):
        
        DER-encoded private_key
        private_key
        plaintext
        
        If a supported authentication method cannot be determined, the connection will
        not be initiated.
        """
        try:
            # Check to see if this hostkey exists in known_hosts, and if not:
            # - set cnopts.hostkeys to None (to allow the new host connection);
            # - get the hostkey after connecting;
            # - update known_hosts with the new value.
            # Based off of this stackoverflow question:
            #     https://stackoverflow.com/questions/53666106/use-paramiko-autoaddpolicy-with-pysftp
            hostkeys = None
            if self.cnopts.hostkeys.lookup(self.hostName) is None:
                if self.verbose:
                    print('Key for host: ' + self.hostName + ' was not found in known_hosts')
                hostkeys = self.cnopts.hostkeys
                self.cnopts.hostkeys = None

            args = {'host':self.hostName,
                    'username':self.userName,
                    'cnopts':self.cnopts}

            # Determine what type of authentication to use
            if hasattr(self, 'private_key') and hasattr(self, 'private_key_password'):
                if self.verbose:
                    print('Using public key authentication with DER-encoded private key')
                args['private_key'] = self.private_key
                args['private_key_pass'] = self.private_key_password
            elif hasattr(self, 'private_key') and not hasattr(self, 'password'):
                if self.verbose:
                    print('Using public key authentication with plaintext private key')
                args['private_key'] = self.private_key
            elif hasattr(self, 'password'):
                if self.verbose:
                    print('Using plaintext authentication')
                args['password'] = self.password
            else:
                raise ssh_exception.BadAuthenticationType('No supported authentication methods available', ['password', 'public_key'])

            # connect using the authentication type determined above
            if self.verbose:
                print('Connecting using arguments: ' + str(args))
            self.connection = pysftp.Connection(**args)

            # Save the new hostkey to known_hosts
            if hostkeys is not None:
                if self.verbose:
                    print('Appending new hostkey for ' + self.hostName + ' to known_hosts, and writing to disk...')
                hostkeys.add(self.hostName, self.connection.remote_server_key.get_name(), self.connection.remote_server_key)
                hostkeys.save(pysftp.helpers.known_hosts())
        except Exception as e:
            print(str(e))

    def is_connected(self):
        """Check the connection (using the listdir() method) to confirm that it's active."""
        if hasattr(self, 'connection'):
            if self.connection.listdir():
                return True
        return None

    # region Commands Section
    def execute_command(self, cmd):
        """Find and execute the command in Commands class"""
        parts = cmd.split(' ')
        try:
            return getattr(self, parts[0])(parts[1:])
        except AttributeError as e:
            raise ValueError("Command not found, try 'help'") from e

    @staticmethod
    def quit(_args):
        """quit the client"""
        quit(0)

    @staticmethod
    def help(args):
        """Show command list, or help file for requested command"""
        if len(args) is 0:
            print_help("command_list.txt")
        else:
            print_help(args[0] + "_help.txt")
    # endregion

    def __del__(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass


def print_help(file):
    """Prints help files with consistent formatting"""
    try:
        with open(file) as text:
            for line in iter(lambda: text.readline(), ''):
                parts = line.strip().split('@')
                line_output = ''
                for part in parts[:2]:
                    line_output += ('{:<' + str(HELP_COMMAND_SPACING) + 's}').format(part)
                if len(line_output.strip()) > 0:
                    print(line_output)
    except FileNotFoundError as e:
        raise FileNotFoundError("Missing help file") from e


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        main(capture_arguments())
