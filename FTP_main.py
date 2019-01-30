import argparse
import pysftp as sftp


def capturingArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help="Input host name", required=True)
    parser.add_argument('-U', '--username', help='input username', required=True)
    parser.add_argument('-P', '--password', help='input password', required=True)
    arguments = parser.parse_args()
    return arguments


class sftp(object):
    def __init__(self, args):
        self.args = vars(args)
        self.hostName = self.args['host']
        self.userName = self.args['username']
        self.password = self.args['password']

    def initiateConnection(self):
        '''Does initialize connection using  host name, user name & password'''
        try:
            self.connection = sftp.Connection(host=self.hostName, username=self.userName, password=self.password)
        except Exception as e:
            print(str(e))

    def __del__(self):
        self.connection.close()


if __name__ == '__main__':
    arguments = capturingArguments()
    sftp = sftp(arguments)
