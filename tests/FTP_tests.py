#!/usr/bin/env python3

import sys
from os import path
import unittest
from unittest import main
import warnings

# fix for running as script?
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from SFTPClient.Client import SFTP
from FTP_auth import PSU_ID, PSU_CECS_PASSWORD, PRIVATE_KEY_PASSWORD


class SFTPTestCase(unittest.TestCase):
    """SFTPTestCase class provides a unittest class used for testing the SFTP class
    
        Unit tests can be run using the following command:
        
        python3 -m unittest -v FTP_tests.py
    """
    def __init__(self, *args, **kwargs):
        super(SFTPTestCase, self).__init__(*args, **kwargs)
        
        self.sftp_client = None
        self.verbose = None
        self.hostname = 'linuxlab.cs.pdx.edu'
        self.username = PSU_ID
        self.password = PSU_CECS_PASSWORD
        self.private_key_password = PRIVATE_KEY_PASSWORD
        # file name used for testing the 'ls' command
        self.test_file_name = 'SFTPTestCase_file.txt'
        # directory name/path used for testing the 'ls' command
        self.test_dir_name = 'SFTPTestCase_dir'
        
        if 'test_plaintext_auth' in args:
            # perform plaintext authentication if requested
            self.sftp_args = {'hostname':self.hostname, 'username':self.username, 'password':self.password}
        else:
            # by default, perform public key authentication
            self.sftp_args = {'hostname':self.hostname, 'username':self.username, 'private_key_password':self.private_key_password}

    def setUp(self):
        """Test suite setUp"""
        # perform a sanity check to confirm that the sftp_client member is uninitialized
        self.assertIsNone(self.sftp_client, SFTP)
        self.assertNotIsInstance(self.sftp_client, SFTP)
        
        # initialize sftp_client
        self.sftp_client = SFTP(**self.sftp_args)
        self.assertIsNotNone(self.sftp_client, SFTP)
        self.assertIsInstance(self.sftp_client, SFTP)
    
    def tearDown(self):
        """Test suite tearDown"""
        # TODO: should we perform a proper disconnect when doing a tearDown()?
        self.sftp_client = None

    def test_plaintext_auth(self):
        """Test plaintext authentication"""
        self.assertTrue(self.sftp_client.is_connected())

    def test_public_key_auth(self):
        """Test public key authentication"""
        self.assertTrue(self.sftp_client.is_connected())

    def test_list_command(self):
        """Test the 'ls' command"""
        # perform a sanity check to confirm that the sftp_client member is initialized and connected
        self.assertTrue(self.sftp_client.is_connected())

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
        
        result = None
        
        # Test list command with 1 argument (a file that is known to exist) to:
        #  confirm that the test will fail with an exception when listing a file
        #
        # TODO: this test should be run after creating 'self.test_file_name' using the 'put' command test
        # TODO: this test should be run before the 'rm' command test (which will remove 'self.test_file_name')
        # That way, we'd be guaranteed to have the file exist without prior intervention,
        #   and this would also allow for the delete test to be used to cleanup
        #   In the interim, you will need to create this file manually to allow the test to pass.
        with self.assertRaises(FileNotFoundError):
            result = self.sftp_client.ls([self.test_file_name])

        # Test list command with 1 argument (a directory that doesn't exist) to:
        #  confirm that the test will fail with an exception when listing non-existent directories
        with self.assertRaises(FileNotFoundError):
            result = self.sftp_client.ls(['0xdeadbeef'])
        
        # Test list command with incorrect number of arguments (> 2) to:
        #   confirm that the result is None
        with self.assertRaises(TypeError):
            result = self.sftp_client.ls(['0xdeadbeef', '0xdeadbeef', '0xdeadbeef'])
            
        self.assertIsNone(result)

    def test_chmod_command(self):
        """Test the 'chmod' command"""
        # perform a sanity check to confirm that the sftp_client member is initialized and connected
        self.assertTrue(self.sftp_client.is_connected())
        result = None

        # Test the chmod command with zero arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            result = self.sftp_client.chmod([])

        # Test the chmod command with more than two arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            result = self.sftp_client.chmod(['0xdeadbeef', '0xdeadbeef', '0xdeadbeef'])

        # Test the chmod command with an invalid remotepath to:
        #  confirm that the test will fail with an IOError exception
        with self.assertRaises(IOError):
            result = self.sftp_client.chmod(['0xdeadbeef', 777])

        # Test the chmod command with an invalid mode to:
        #  confirm that the test will fail with a ValueError exception
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        with self.assertRaises(ValueError):
            result = self.sftp_client.chmod([self.test_dir_name, '0xdeadbeef'])

        # Test the chmod command with a valid mode of 000:
        #  confirm that the test will complete without exception;
        #  confirm that an 'ls' of the directory will fail with a PermissionError exception
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        result = self.sftp_client.chmod([self.test_dir_name, 000])
        self.assertIsNone(result)

        # after changing the mode to 000, confirm that the directory is not listable
        with self.assertRaises(PermissionError):
            result = self.sftp_client.ls([self.test_dir_name])

        # Test the chmod command with a valid mode of 755:
        #  confirm that the test will complete without exception;
        #  confirm that an 'ls' of the directory return (empty) results
        #
        # TODO: this test should be run after creating 'self.test_dir_name' using the 'mkdir' command
        #   That way, we'd be guaranteed to have the directory exist prior to running
        #   In the interim, you will need to create this directory manually to allow the test to pass.
        result = self.sftp_client.chmod([self.test_dir_name, 755])
        self.assertIsNone(result)

        # after changing the mode to 755, confirm that the directory is listable
        result = self.sftp_client.ls([self.test_dir_name])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) is 0)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(SFTPTestCase('test_plaintext_auth'))
    suite.addTest(SFTPTestCase('test_public_key_auth'))
    suite.addTest(SFTPTestCase('test_list_command'))
    suite.addTest(SFTPTestCase('test_chmod_command'))
    return suite


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite())
