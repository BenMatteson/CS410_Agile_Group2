import unittest
from unittest.mock import patch, call, MagicMock
from FTP_main.FTP_main import SFTP
from FTP_main.FTP_main import capture_arguments


class Test_SFTP(unittest.TestCase):
    def setUp(self):
        args = MagicMock()
        self.myClass = SFTP(args)

    def tearDown(self):
        pass


@patch("FTP_main.FTP_main.argparse.ArgumentParser", autospec=True)
class Testcapture_arguments(unittest.TestCase):
    def test_capture_arguments(self, mockadd_argument):
        #Actual
        capture_arguments()
        #verify
        addArgs = [call(),
                   call().add_argument('-H', '--host', help='Input host name', required=True),
                   call().add_argument('-U', '--username', help='input username', required=True),
                   call().add_argument('-P', '--password', help='input password', required=True),
                   call().parse_args()]
        mockadd_argument.assert_has_calls(addArgs)

'''
def capture_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', '--host', help='Input host name', required=True)
    parser.add_argument('-U', '--username', help='input username', required=True)
    parser.add_argument('-P', '--password', help='input password', required=True)
    arguments = parser.parse_args()
    return arguments
    
'''

@patch("FTP_main.FTP_main.SFTP.pysftp.hostkeys", autospec=True)
@patch("FTP_main.FTP_main.SFTP.pysftp.Connection", autospec=True)
class Testinitiate_connection(Test_SFTP):
    def test_initiate_connection(self, mockConnection, mockhostkeys):
        #Actual
        self.myClass.initiate_connection()
        #verify
        mockhostkeys.assert_called_once_with(self.myClass)
        mockConnection.assert_called_once_with("host", "username", "password", "cnopts")


if __name__ == '__main__':
    unittest.main()