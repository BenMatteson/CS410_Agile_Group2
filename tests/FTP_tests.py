#!/usr/bin/env python3

import sys
from os import path, remove, rmdir
import unittest
from unittest import main
import warnings
import argparse

# fix for running as script?
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from SFTPClient.Client import SFTP
from SFTPClient.Client import DOWNLOADS_DIRECTORY
from FTP_auth import PSU_ID, PSU_CECS_PASSWORD, PRIVATE_KEY_PASSWORD


class SFTPTestCase(unittest.TestCase):
    """SFTPTestCase provides a base unittest class used for testing the SFTP class
    
        Unit tests can be run using the following command:
        
        python3 -m unittest -v FTP_tests.py
    """
    
    @classmethod
    def setUpClass(cls):
        """Test suite class setUp"""
        
        cls.sftp_client = None
        cls.hostname = 'linuxlab.cs.pdx.edu'
        cls.username = PSU_ID
        cls.password = PSU_CECS_PASSWORD
        cls.private_key_password = PRIVATE_KEY_PASSWORD
        # file name used for testing commands
        cls.test_file_name = 'SFTPTestCase_file.txt'
        # directory name/path used for testing commands
        cls.test_dir_name = 'SFTPTestCase_dir'
        
        if cls.__class__.__name__ is '__main__.PlaintextAuthenticationTestCase':
            # perform plaintext authentication if requested
            cls.sftp_args = {'hostname':cls.hostname, 'username':cls.username, 'password':cls.password}
        else:
            # by default, perform public key authentication
            cls.sftp_args = {'hostname':cls.hostname, 'username':cls.username, 'private_key_password':cls.private_key_password}

        # initialize sftp_client
        cls.sftp_client = SFTP(**cls.sftp_args)

    @classmethod
    def tearDownClass(cls):
        # TODO: should we perform a proper disconnect when doing a tearDown()?
        cls.sftp_client = None
        if path.exists(DOWNLOADS_DIRECTORY):
            rmdir(DOWNLOADS_DIRECTORY)


class PlaintextAuthenticationTestCase(SFTPTestCase):
    """PlaintextAuthenticationTestCase provides a unittest class used for testing plaintext SFTP auth"""
    
    def test_plaintext_auth(self):
        """Test plaintext authentication"""
        self.assertIsNotNone(self.sftp_client, SFTP)
        self.assertIsInstance(self.sftp_client, SFTP)
        self.assertTrue(self.sftp_client.is_connected())


class PublicKeyAuthenticationTestCase(SFTPTestCase):
    """PublicKeyAuthenticationTestCase provides a unittest class used for testing publickey SFTP auth"""
    
    def test_public_key_auth(self):
        """Test public key authentication"""
        self.assertIsNotNone(self.sftp_client, SFTP)
        self.assertIsInstance(self.sftp_client, SFTP)
        self.assertTrue(self.sftp_client.is_connected())


class ListCommandTestCase(SFTPTestCase):
    """ListCommandTestCase class provides a unittest class used for testing the SFTP list command"""

    def test_list_file(self):
        """Test list command with a file that is known to exist"""
        # Test list command with 1 argument (a file that is known to exist) to:
        #  confirm that the test will fail with an exception when listing a file
        #
        # TODO: this test should be run after creating 'self.test_file_name' using the 'put' command test
        # TODO: this test should be run before the 'rm' command test (which will remove 'self.test_file_name')
        # That way, we'd be guaranteed to have the file exist without prior intervention,
        #   and this would also allow for the delete test to be used to cleanup
        #   In the interim, you will need to create this file manually to allow the test to pass.
        result = None
        with self.assertRaises(FileNotFoundError):
            result = self.sftp_client.ls([self.test_file_name])
        self.assertIsNone(result)

    def test_list_nonexistent(self):
        """Test list command with a file that is non-existent"""
        # Test list command with 1 argument (a directory that doesn't exist) to:
        #  confirm that the test will fail with an exception when listing non-existent directories
        result = None
        with self.assertRaises(FileNotFoundError):
            result = self.sftp_client.ls(['0xdeadbeef'])
        self.assertIsNone(result)
        
    def test_list_incorrect_args(self):
        """Test list command with an incorrect number of arguments (>2)"""
        # Test list command with incorrect number of arguments (> 2) to:
        #   confirm that the test will fail with a TypeError exception;
        #   confirm that the result is None
        result = None
        with self.assertRaises(TypeError):
            result = self.sftp_client.ls(['0xdeadbeef', '0xdeadbeef', '0xdeadbeef'])
        self.assertIsNone(result)
        
    def test_list_zero_arg(self):
        """Test list command with zero arguments"""
        # Test the list command with zero arguments to:
        #  confirm that it returns a result;
        #  confirm that the result is a list;
        #  confirm that the result contains 'self.test_dir_name'
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running.
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        result = None
        result = self.sftp_client.ls([])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertIn(self.test_dir_name, result)
        
    def test_list_one_arg(self):
        """Test list command with one argument"""
        # Test the list command with 1 argument (an empty directory that is known to exist) to:
        #  confirm that it returns a result;
        #  confirm that the result is a list;
        #  confirm that the result is an empty list
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        result = None
        result = self.sftp_client.ls([self.test_dir_name])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) is 0)


class ChmodCommandTestCase(SFTPTestCase):
    """ChmodCommandTestCase class provides a unittest class used for testing the SFTP chmod command"""
    
    def test_chmod_zero_arg(self):
        """Test chmod command with zero arguments"""
        # Test the chmod command with zero arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.chmod([])

    def test_chmod_three_arg(self):
        """Test chmod command with three arguments"""
        # Test the chmod command with more than two arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.chmod(['0xdeadbeef', '0xdeadbeef', '0xdeadbeef'])

    def test_chmod_invalid_path(self):
        """Test chmod command with an invalid remotepath"""
        # Test the chmod command with an invalid remotepath to:
        #  confirm that the test will fail with an IOError exception
        with self.assertRaises(IOError):
            self.sftp_client.chmod(['0xdeadbeef', 777])

    def test_chmod_invalid_mode(self):
        """Test chmod command with an invalid mode"""
        # Test the chmod command with an invalid mode to:
        #  confirm that the test will fail with a ValueError exception
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        with self.assertRaises(ValueError):
            self.sftp_client.chmod([self.test_dir_name, '0xdeadbeef'])

    def test_chmod_mode_000(self):
        """Test chmod command with a mode of 000"""
        # Test the chmod command with a valid mode of 000:
        #  confirm that the test will complete without exception;
        #  confirm that an 'ls' of the directory will fail with a PermissionError exception
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        result = None
        self.sftp_client.chmod([self.test_dir_name, 000])
        with self.assertRaises(PermissionError):
            result = self.sftp_client.ls([self.test_dir_name])
        self.assertIsNone(result)

    def test_chmod_mode_755(self):
        """Test chmod command with a mode of 755"""
        # Test the chmod command with a valid mode of 755:
        #  confirm that the test will complete without exception;
        #  confirm that an 'ls' of the directory return (empty) results
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        self.sftp_client.chmod([self.test_dir_name, 755])

        # after changing the mode to 755, confirm that the directory is listable
        result = self.sftp_client.ls([self.test_dir_name])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) is 0)

class GetCommandTestCase(SFTPTestCase):
    """GetCommandTestCase class provides a unittest class used for testing the SFTP get command"""

    def test_get_zero_arg(self):
        """Test get command with zero arguments"""
        # Test the get command with zero arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.get([])

    def test_get_one_arg(self):
        """Test get command with one argument"""
        # Test the get command with one argument to:
        #  confirm that the remote file is downloaded to DOWNLOADS_DIRECTORY
        file_name = "SFTP_test_get_one_arg.txt"
        localpath = path.join(DOWNLOADS_DIRECTORY, file_name)
        self.sftp_client.connection.execute(f"printf '{file_name}' > {file_name}")
        self.sftp_client.get([file_name])
        file_text = None
        with open(localpath, "r") as f:
            file_text = f.read()
        self.assertEqual(file_name, file_text)
        self.sftp_client.connection.remove(file_name)
        remove(localpath)
        
    def test_get_one_arg_no_such_remote_file(self):
        """Test get command with one invalid argument"""
        # Test the get command with one argument to:
        #  confirm that the test will fail with an IOError exception
        file_name = "SFTP_this_file_does_not_exist.txt"
        with self.assertRaises(IOError):
            self.sftp_client.get([file_name])
        
    def test_get_two_arg(self):
        """Test get command with two argument"""
        # Test the get command with two argument to:
        #  confirm that the remote file is downloaded to the localpath
        file_name = "SFTP_test_get_two_arg.txt"
        localpath = path.expanduser(path.join('~', 'Desktop', file_name))
        self.sftp_client.connection.execute(f"printf '{file_name}' > {file_name}")
        self.sftp_client.get([file_name, localpath])
        file_text = None
        with open(localpath, "r") as f:
            file_text = f.read()
        self.assertEqual(file_name, file_text)
        self.sftp_client.connection.remove(file_name)
        remove(localpath)
        
    def test_get_two_arg_no_such_remote_file(self):
        """Test get command with two arguments where the first is an invalid remotepath"""
        # Test the get command with an invalid remotepath to:
        #  confirm that the test will fail with an IOError exception
        file_name = "SFTP_this_file_does_not_exist.txt"
        localpath = path.expanduser(path.join('~', 'Desktop', file_name))
        with self.assertRaises(IOError):
            self.sftp_client.get([file_name, localpath])

    def test_get_two_arg_no_such_localpath(self):
        """Test get command with two arguments where the second is an invalid localpath"""
        # Test the get command with an invalid localpath to:
        #  confirm that the test will fail with an IOError exception
        file_name = "SFTP_test_get_two_arg_no_such_localpath.txt"
        localpath = path.join("SFTP","this", "localpath", "does", "not", "exist")
        self.sftp_client.connection.execute(f"printf '{file_name}' > {file_name}")
        with self.assertRaises(IOError):
            self.sftp_client.get([file_name, localpath])
        self.sftp_client.connection.remove(file_name)

    def test_get_three_arg(self):
        """Test get command with three arguments"""
        # Test the get command with more than two arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.get(["file1", "file2", "file3"])

def suite():
    suite = unittest.TestSuite()
    
    suite.addTest(PlaintextAuthenticationTestCase('test_plaintext_auth'))
    
    suite.addTest(PublicKeyAuthenticationTestCase('test_public_key_auth'))
    
    suite.addTest(ListCommandTestCase('test_list_file'))
    suite.addTest(ListCommandTestCase('test_list_nonexistent'))
    suite.addTest(ListCommandTestCase('test_list_incorrect_args'))
    suite.addTest(ListCommandTestCase('test_list_zero_arg'))
    suite.addTest(ListCommandTestCase('test_list_one_arg'))
    
    suite.addTest(ChmodCommandTestCase('test_chmod_zero_arg'))
    suite.addTest(ChmodCommandTestCase('test_chmod_three_arg'))
    suite.addTest(ChmodCommandTestCase('test_chmod_invalid_path'))
    suite.addTest(ChmodCommandTestCase('test_chmod_invalid_mode'))
    suite.addTest(ChmodCommandTestCase('test_chmod_mode_000'))
    suite.addTest(ChmodCommandTestCase('test_chmod_mode_755'))
    
    suite.addTest(GetCommandTestCase('test_get_zero_arg'))
    suite.addTest(GetCommandTestCase('test_get_one_arg'))
    suite.addTest(GetCommandTestCase('test_get_one_arg_no_such_remote_file'))
    suite.addTest(GetCommandTestCase('test_get_two_arg'))
    suite.addTest(GetCommandTestCase('test_get_two_arg_no_such_remote_file'))
    suite.addTest(GetCommandTestCase('test_get_two_arg_no_such_localpath'))
    suite.addTest(GetCommandTestCase('test_get_three_arg'))
    
    return suite


if __name__ == '__main__':
    # parse CLI arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='Verbose logging', required=False, action='store_true')
    parser.set_defaults(verbose=None)
    arguments = parser.parse_args()
    
    # set verbosity
    if arguments.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # run the tests
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        runner.run(suite())
