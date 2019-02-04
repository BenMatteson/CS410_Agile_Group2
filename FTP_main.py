import argparse
import pysftp
import sys

HELP_TAB_SPACING = 10
TAB_SIZE = 4  # I can't figure out if there's a way to read this value, 'cause I think it varies...

def capturingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Input host name', required=True)
    parser.add_argument('-U', '--username', help='input username', required=True)
    parser.add_argument('-P', '--password', help='input password', required=True)
    arguments = parser.parse_args()
    return arguments


class Sftp(object):
    def __init__(self, args):
        self.args = vars(args)
        self.hostName = self.args['host']
        self.userName = self.args['username']
        self.password = self.args['password']
        self.connection = None

    def initiateConnection(self):
        """Does initialize connection using  host name, user name & password"""
        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # allows connection to any host
            self.connection = pysftp.Connection(host=self.hostName, username=self.userName, password=self.password, cnopts=cnopts)
        except Exception as e:
            print(str(e))

    def __del__(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except:
                pass


def printHelp(file):
    """Prints help files with consistent formatting"""
    with open(file) as text:
        for line in iter(lambda: text.readline(), ''):
            parts = line.strip().split('@')
            spacing = HELP_TAB_SPACING - (len(parts[0].strip()) // TAB_SIZE)
            line_output = ''
            for part in parts:
                line_output += (part.strip() + ('\t' * spacing))
            print(line_output.strip())


class Commands:
    """
    Collection of commands that can be executed.
    All commands should have the same argument list, though any number may be unused.
    """

    @staticmethod
    def executeCommand(cmd, connection):
        """Find and execute the command in Commands class"""
        parts = cmd.split(' ')
        try:
            return getattr(Commands, parts[0])(parts[1:], connection)
        except AttributeError:
            raise ValueError()

    @staticmethod
    def quit(_args, _connection):
        """quit the client"""
        quit(0)

    @staticmethod
    def help(args, _connection):
        """Show command list, or help file for requested command"""
        if len(args) is 0:
            printHelp("command_list.txt")
        else:
            printHelp(args[0] + "_help.txt")


if __name__ == '__main__':
    arguments = capturingArguments()
    sftp = Sftp(arguments)
    sftp.initiateConnection()
    if sftp.connection is not None:
        print("Connection Successful!\n"
              "Type a command or 'help' to see available commands")
    else:
        print("Unable to connect, please check your connection information")
        quit(1)
    while True:
        try:
            command = input('> ')
            Commands.executeCommand(command, sftp)
        except ValueError:
            print("Command not found, try 'help'")
            continue
