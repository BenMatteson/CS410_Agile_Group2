#!/usr/bin/env python3
import argparse
import logging
import warnings
import shlex
import getpass

import paramiko

from SFTPClient import Client

HELP_COMMAND_SPACING = 35  # Max length(+1) of sample commands in help files
HELP_FILE_LOCATION = "help_files/"

MAX_AUTH_TRIES = 3

class ExitRequested(Exception):
    pass


def main():
    args = vars(capture_arguments())

    if args['verbose']:
        logging.basicConfig(level=logging.DEBUG)

    cli = None
    prompt = True
    while prompt:
        try:
            if cli is None:
                # attempt to connect using whatever arguments we've got
                cli = SFTPCLI(Client.SFTP(args['host'], args['username'], args['password'], args['private_key_password']))
            command = input('> ')
            # execute command, handle result accordingly.
            if command:
                result = cli.execute_command(command)
                if isinstance(result, list):
                    for item in result:
                        print(item)
                elif isinstance(result, str):
                    print(result)
        except (paramiko.SSHException) as e:
            if str(e) == 'not a valid DSA private key file':
                # potentially an encrypted private key?
                # prompt the user for the private key password a few times
                logging.debug('Private key is encrypted - prompting for password...')
                for i in range(0,MAX_AUTH_TRIES):
                    print("CLI: " + str(cli))
                    print("SFTP: " + str(cli.sftp))
                    try:
                        private_key_password = getpass.getpass("Enter passphrase for private key:")
                        cli.sftp.private_key_password = private_key_password
                        cli.sftp.connection = cli.sftp.initiate_connection()
                    except (paramiko.SSHException):
                        # wrong password?
                        pass
                    if cli.sftp is not None and cli.sftp.is_connected():
                        break
            
                # if public key auth fails, prompt the user for the plaintext password
                if cli.sftp.connection is None:
                    logging.debug('Public key authentication failed - falling back to password auth...')
                    for i in range(0,MAX_AUTH_TRIES):
                        try:
                            password = getpass.getpass()
                            # attempt to connect
                            cli.sftp.password = password
                            cli.sftp.connection = cli.sftp.initiate_connection()
                        except (paramiko.SSHException):
                            # wrong password?
                            cli.sftp.password = None
                        if cli.sftp is not None and cli.sftp.is_connected():
                            break
                    break
            else:
                print(e)
                continue
        except (ValueError, FileNotFoundError, TypeError, PermissionError, IOError) as e:
            print(e)
            continue
        except ExitRequested:
            prompt = False
            cli = None
    return 0


def capture_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Input host name', required=False)
    parser.add_argument('-U', '--username', help='input username', required=False)
    parser.add_argument('-P', '--password', help='input password', required=False)
    parser.add_argument('-p', '--private_key_password', help='Passphrase required to decrypt private key', required=False)
    parser.add_argument('-v', '--verbose', help='Verbose logging', required=False, action='store_true')
    parser.set_defaults(verbose=None)
    arguments = parser.parse_args()
    return arguments


class SFTPCLI(object):
    def __init__(self, sftp=None):
        self.sftp = sftp

    def execute_command(self, cmd):
        """Find and execute the command"""
        cli_commands = {'help', 'quit'}
        parts = shlex.split(cmd)
        if cli_commands.__contains__(parts[0]):
            return getattr(self, parts[0])(parts[1:])
        else:
            if parts[0] == 'connect' or self.sftp is not None and self.sftp.is_connected():
                try:
                    temp = getattr(self.sftp, parts[0])(parts[1:])
                    return temp
                except AttributeError as e:
                    raise ValueError("Command not found, try 'help'") from e
            else:
                print("Not connected - see 'help connect'")

    def help(self, args):
        """Show command list, or help file for requested command"""
        if len(args) is 0:
            self.print_help(HELP_FILE_LOCATION + "command_list.txt")
        else:
            self.print_help(HELP_FILE_LOCATION + args[0] + "_help.txt")

    @staticmethod
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

    @staticmethod
    def quit(_args):
        raise ExitRequested()


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        exit(main())
