#!/usr/bin/env python3
import argparse
import logging
import warnings

import paramiko

from SFTPClient import Client

HELP_COMMAND_SPACING = 35  # Max length(+1) of sample commands in help files
HELP_FILE_LOCATION = "help_files/"


class ExitRequested(Exception):
    pass


def main():
    args = vars(capture_arguments())

    if args['verbose']:
        logging.basicConfig(level=logging.DEBUG)
    host_name = args['host']
    user_name = args['username']

    password = None
    if 'password' in args and args['password'] is not None:
        # the user supplied password input
        password = args['password']

    private_key_password = None
    if 'private_key_password' in args and args['private_key_password'] is not None:
        # the user supplied private key password input
        private_key_password = args['private_key_password']

    try:
        cli = SFTPCLI(host_name, user_name, password, private_key_password)
    except paramiko.SSHException:
        print("Unable to connect, please check user and server info.")
        exit(1)


    prompt = True
    while prompt:
        try:
            command = input('> ')
            # execute command, handle result accordingly.
            result = cli.execute_command(command)
            if isinstance(result, list):
                # TODO pretty print lists
                print(result)
            elif isinstance(result, str):
                print(str)
        except (ValueError, FileNotFoundError) as e:
            print(e)
            continue
        except ExitRequested:
            prompt = False
            cli = None
    exit(0)


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


class SFTPCLI(object):
    def __init__(self, hostname, username, password=None, private_key_password=None):
        self.sftp = Client.SFTP(hostname, username, password, private_key_password)
        print("Connection Successful!\n"
              "Type a command or 'help' to see available commands")

    def execute_command(self, cmd):
        """Find and execute the command"""
        cli_commands = {'help', 'quit'}
        parts = cmd.split(' ')
        if cli_commands.__contains__(parts[0]):
            return getattr(self, parts[0])(parts[1:])
        else:
            try:
                temp = getattr(self.sftp, parts[0])(parts[1:])
                return temp
            except AttributeError as e:
                raise ValueError("Command not found, try 'help'") from e

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
        main()
