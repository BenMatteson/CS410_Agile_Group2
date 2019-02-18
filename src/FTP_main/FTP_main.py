import argparse
import warnings

import pysftp

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
    parser.add_argument('-P', '--password', help='input password', required=True)
    arguments = parser.parse_args()
    return arguments


class SFTP(object):
    def __init__(self, args):
        self.args = vars(args)

    def initiate_connection(self):
        """Does initialize connection using  host name, user name & password"""
        self.hostName = self.args['host']
        self.userName = self.args['username']
        self.password = self.args['password']
        self.connection = None

        try:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # allows connection to any host
            self.connection = pysftp.Connection(host=self.hostName,
                                                username=self.userName,
                                                password=self.password,
                                                cnopts=cnopts)
        except Exception as e:
            print(str(e))


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

'''
    def deleteConnection(self):
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
'''

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
