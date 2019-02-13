#!/usr/bin/env python3

import unittest
from FTP_main import SFTP
from FTP_auth import PSU_ID, PSU_CECS_PASSWORD, PRIVATE_KEY_PASSWORD

class SFTPTestInfo(dict):
    """This class exists because the SFTP class initializes itself using an object,
        and that object needs to respond to calls to the __dict__() method because it's passed to vars()
        
        There is probably an easier way to do this?
    """
    def __init__(self, dict):
        self.__dict__.update(dict)

class SFTPTestCase(unittest.TestCase):
    """SFTPTestCase class provides a unittest class used for testing the SFTP class
    
        Unit tests can be run using the following command:
        
        python3 -m unittest -v FTP_tests.py
    """
    def setUp(self):
        pass
    
    def tearDown(self):
        #self.sftp_client.dispose() # this was in the documentation, not sure where it comes from - maybe an example custom class method?
        self.sftp_client = None

    def test_plaintext_auth(self):
        verbose = None
        hostname = 'linuxlab.cs.pdx.edu'
        username = PSU_ID
        password = PSU_CECS_PASSWORD
        args = {'verbose': verbose, 'host':hostname, 'username':username, 'password':password}
        self.sftp_client = SFTP(SFTPTestInfo(args))
        self.sftp_client.initiate_connection()
        self.assertTrue(self.sftp_client.is_connected())

    def test_private_key_auth(self):
        verbose = None
        hostname = 'linuxlab.cs.pdx.edu'
        username = PSU_ID
        private_key_password = PRIVATE_KEY_PASSWORD
        args = {'verbose': verbose, 'host':hostname, 'username':username, 'private_key_password':private_key_password}
        self.sftp_client = SFTP(SFTPTestInfo(args))
        self.sftp_client.initiate_connection()
        
        self.assertTrue(self.sftp_client.is_connected())

def suite():
    suite = unittest.TestSuite()
    suite.addTest(SFTPTestCase('test_plaintext_auth'))
    suite.addTest(SFTPTestCase('test_private_key_auth'))
    return suite
