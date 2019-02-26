from SFTPClient.Client import SFTP

import unittest
from unittest.mock import patch, MagicMock, call, ANY


class Test_Client(unittest.TestCase):
    def setUp(self):
        self.local_directory = MagicMock()
        SFTP.connection = MagicMock()
        SFTP.initiate_connection = MagicMock()
        self.myClass = SFTP("hostname", "username", "password", "public_key")

    def tearDown(self):
        pass


class Testis_connected(Test_Client):
    def test_is_connected(self):
        # setup
        self.myClass.connection.listdir.return_value = True
        # actual
        actual = self.myClass.is_connected()
        # verify
        self.myClass.connection.listdir.assert_called_once_with()
        self.assertTrue(actual)

    def test_Test_Client1(self):
        # setup
        self.myClass.connection.listdir.return_value = False
        # actual
        actual = self.myClass.is_connected()
        # verify
        self.myClass.connection.listdir.assert_called_once_with()
        self.assertFalse(actual)


class Testping(Test_Client):
    def test_ping(self):
        # setup
        self.myClass.connection.listdir.return_value = True
        # actual
        actual = self.myClass.ping()
        # verify
        self.myClass.connection.listdir.assert_called_once_with()
        self.assertEqual(actual, "pong")

    def test_ping1(self):
        # setup
        self.myClass.connection.listdir.return_value = False
        # actual
        actual = self.myClass.ping()
        # verify
        self.myClass.connection.listdir.assert_called_once_with()
        self.assertEqual(actual, "nothing happened")


class Testls(Test_Client):
    def test_ls(self):
        # actual
        actual = self.myClass.ls([])
        # verify
        self.myClass.connection.listdir.assert_called_once_with()
        self.assertTrue(actual)

    def test_ls1(self):
        # actual
        actual = self.myClass.ls(["car"])
        # verify
        self.myClass.connection.listdir.assert_called_once_with(("car"))
        self.assertTrue(actual, "car")

    def test_ls2(self):
        # verify
        self.assertRaises(TypeError, self.myClass.ls, ['car', 'boat'])


class Testchmod(Test_Client):
    def test_chmod(self):
        # actual
        self.myClass.chmod(('car', 2))
        # verify
        self.myClass.connection.chmod.assert_called_once_with('car', 2)

    def test_chmod1(self):
        # verify
        self.assertRaises(TypeError, self.myClass.chmod, ['car', 'boat', 'train'])


@patch("SFTPClient.Client.os.getcwd", autospec=True)
@patch("builtins.print", autospec=True)
@patch("SFTPClient.Client.os.listdir", autospec=True)
class Testlsl(Test_Client):
    def test_lsl(self, mocklistdir, mockprint, mockgetcwd):
        # setup
        mockgetcwd.return_value = "/Users/myCurrentDirectory"
        mocklistdir.side_effect = iter(["file1"])
        # actual
        self.myClass.lsl()
        # verify
        printCalls = [call("f"), call("i"), call("l"), call("e"), call("1")]
        mockprint.assert_has_calls(printCalls)


@patch("builtins.exit", autospec=True)
class TestcloseAndExit(Test_Client):
    def test_closeAndExit(self, mockexit):
        # actual
        self.myClass.closeAndExit()
        #verify
        self.myClass.connection.close.assert_called_once_with()
        mockexit.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()