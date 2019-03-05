#!/usr/bin/env python3
import sys
import os
import shutil
import unittest
import warnings
import argparse
import re

# fix for running as script(if project root not in PYTHONPATH)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from SFTPClient.Client import SFTP
from SFTPClient.Client import DOWNLOADS_DIRECTORY, HISTORY_FILE
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
        cls.sftp_client = None
        if os.path.exists(DOWNLOADS_DIRECTORY):
            shutil.rmtree(DOWNLOADS_DIRECTORY)

    def assertExists(self, item, msg=None):
            """Fail the test unless item exists on the remote SFTP server."""
            if not self.sftp_client.connection.exists(item):
                msg = self._formatMessage(msg, "%s does not exist on remote server" % item)
                raise self.failureException(msg)

    def assertExists(self, item, msg=None):
            """Fail the test unless item exists on the remote SFTP server."""
            if not self.sftp_client.connection.exists(item):
                msg = self._formatMessage(msg, "%s does not exist on remote server" % item)
                raise self.failureException(msg)


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
    def setUp(self):
        self.sftp_client.connection.execute('touch ' + self.test_file_name)
        self.sftp_client.connection.execute('mkdir ' + self.test_dir_name)

    def tearDown(self):
        self.sftp_client.connection.execute('rm ' + self.test_file_name)
        self.sftp_client.connection.execute('rmdir ' + self.test_dir_name)

    def test_list_file(self):
        """Test list command with a file that is known to exist"""
        # Test list command with 1 argument (a file that is known to exist) to:
        #  confirm that the test will fail with an exception when listing a file
        self.sftp_client.connection.open(self.test_file_name, 'w')
        result = None
        with self.assertRaises(FileNotFoundError):
            result = self.sftp_client.ls([self.test_file_name])
        self.assertIsNone(result)
        self.sftp_client.connection.remove(self.test_file_name)

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
        result = self.sftp_client.ls([self.test_dir_name])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) is 0)


class ChmodCommandTestCase(SFTPTestCase):
    """ChmodCommandTestCase class provides a unittest class used for testing the SFTP chmod command"""
    def setUp(self):
        self.sftp_client.connection.execute('mkdir ' + self.test_dir_name)

    def tearDown(self):
        self.sftp_client.connection.execute('rmdir ' + self.test_dir_name)

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
        with self.assertRaises(ValueError):
            self.sftp_client.chmod([self.test_dir_name, '0xdeadbeef'])

    def test_chmod_invalid_int_mode(self):
        """Test chmod command with an invalid integer mode"""
        # Test the chmod command with an invalid mode to:
        #  confirm that the test will fail with a ValueError exception
        with self.assertRaises(ValueError):
            self.sftp_client.chmod([self.test_dir_name, 999])

    def test_chmod_mode_000(self):
        """Test chmod command with a mode of 000"""
        # Test the chmod command with a valid mode of 000:
        #  confirm that the test will complete without exception;
        #  confirm that an 'ls' of the directory will fail with a PermissionError exception
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
        localpath = os.path.join(DOWNLOADS_DIRECTORY, file_name)
        self.sftp_client.connection.execute(f"printf '{file_name}' > {file_name}")
        self.sftp_client.get([file_name])
        file_text = None
        with open(localpath, "r") as f:
            file_text = f.read()
        self.assertEqual(file_name, file_text)
        self.sftp_client.connection.remove(file_name)
        os.remove(localpath)

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
        localpath = os.path.expanduser(os.path.join('~', 'Desktop', file_name))
        self.sftp_client.connection.execute(f"printf '{file_name}' > {file_name}")
        self.sftp_client.get([file_name, localpath])
        file_text = None
        with open(localpath, "r") as f:
            file_text = f.read()
        self.assertEqual(file_name, file_text)
        self.sftp_client.connection.remove(file_name)
        os.remove(localpath)

    def test_get_two_arg_no_such_remote_file(self):
        """Test get command with two arguments where the first is an invalid remotepath"""
        # Test the get command with an invalid remotepath to:
        #  confirm that the test will fail with an IOError exception
        file_name = "SFTP_this_file_does_not_exist.txt"
        localpath = os.path.expanduser(os.path.join('~', 'Desktop', file_name))
        with self.assertRaises(IOError):
            self.sftp_client.get([file_name, localpath])

    def test_get_two_arg_no_such_localpath(self):
        """Test get command with two arguments where the second is an invalid localpath"""
        # Test the get command with an invalid localpath to:
        #  confirm that the test will fail with an IOError exception
        file_name = "SFTP_test_get_two_arg_no_such_localpath.txt"
        localpath = os.path.join("SFTP","this", "localpath", "does", "not", "exist")
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


class RmdirCommandTestCase(SFTPTestCase):
    """RmdirCommandTestCase class provides a unittest class used for testing the SFTP rmdir command"""

    def test_rmdir_zero_arg(self):
        """Test rmdir command with zero arguments"""
        # Test the rmdir command with zero arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.rmdir([])

    def test_rmdir_two_arg(self):
        """Test rmdir command with two arguments"""
        # Test the rmdir command with more than one argument to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.rmdir(["dir1", "dir2"])

    def test_rmdir_no_such_dir(self):
        """Test rmdir command with a nonexistent directory"""
        # Test the rmdir command with a non-existent argument to:
        #  confirm that the test will fail with a TypeError exception
        dir_name = "SFTP_this_directory_does_not_exist"
        with self.assertRaises(TypeError):
            self.sftp_client.rmdir([dir_name])

    def test_rmdir_one_empty_dir(self):
        """Test rmdir command with a single empty directory"""
        # Test the rmdir command with an empty directory to:
        #  confirm that rmdir deletes an empty directory
        dir_name = "SFTP_test_rmdir_one_empty_dir"
        self.sftp_client.connection.mkdir(dir_name)
        self.assertTrue(self.sftp_client.connection.isdir(dir_name))
        self.sftp_client.rmdir([dir_name])
        self.assertFalse(self.sftp_client.connection.isdir(dir_name))

    def test_rmdir_wrong_permissions(self):
        """Test rmdir command with a directory withou"""
        # Test the rmdir command with an empty directory without write permissions to:
        #  confirm that the test will fail with a PermissionError exception

        # Create a new directory with wrong permissions
        dir_name = "SFTP_test_rmdir_wrong_permissions"
        self.sftp_client.connection.mkdir(dir_name, 144)
        self.assertTrue(self.sftp_client.connection.isdir(dir_name))

        # Try to delete it
        with self.assertRaises(PermissionError):
            self.sftp_client.rmdir([dir_name])
        self.assertTrue(self.sftp_client.connection.isdir(dir_name))

        # Change the permissions and remove it
        self.sftp_client.connection.chmod(dir_name, 744)
        self.sftp_client.rmdir([dir_name])
        self.assertFalse(self.sftp_client.connection.isdir(dir_name))

    def test_rmdir_one_dir_one_file(self):
        """Test rmdir command with a single directory with one file"""
        # Test the rmdir command with a directory with a file in it to:
        #  confirm that rmdir will delete the file and directory
        dir_name = "SFTP_test_rmdir_one_dir_one_file"
        file_name = "SFTP_file1"

        # Create a new directory
        self.sftp_client.connection.mkdir(dir_name)
        self.assertTrue(self.sftp_client.connection.isdir(dir_name))

        # Add a file to the directory
        self.sftp_client.connection.execute(f"touch {dir_name}/{file_name}")
        self.assertTrue(self.sftp_client.connection.isfile(f"{dir_name}/{file_name}"))

        # Remove the directory
        self.sftp_client.rmdir([dir_name])
        self.assertFalse(self.sftp_client.connection.isdir(dir_name))

    def test_rmdir_one_dir_multiple_files(self):
        """Test rmdir command with a single directory with one file"""
        # Test the rmdir command with a directory with multiple files to:
        #  confirm that rmdir will delete all the files and the directory
        dir_name = "SFTP_test_rmdir_one_dir_multiple_files"
        file_names = ["SFTP_file" + str(i) for i in range(1,5)]

        # Create a new directory
        self.sftp_client.connection.mkdir(dir_name)
        self.assertTrue(self.sftp_client.connection.isdir(dir_name))

        # Add files to the directory
        for file_name in file_names:
            self.sftp_client.connection.execute(f"touch {dir_name}/{file_name}")
            self.assertTrue(self.sftp_client.connection.isfile(f"{dir_name}/{file_name}"))

        # Remove the directory
        self.sftp_client.rmdir([dir_name])
        self.assertFalse(self.sftp_client.connection.isdir(dir_name))

    def test_rmdir_two_nested_dirs(self):
        """Test rmdir command with two directories, one inside the other"""
        # Test the rmdir command with nested directories to:
        #  confirm that rmdir will delete both directories

        # Create first directory
        dir1 = "SFTP_test_rmdir_two_nested_dirs_dir1"
        self.sftp_client.connection.mkdir(dir1)
        self.assertTrue(self.sftp_client.connection.isdir(dir1))

        # Create second directory
        dir2 = "SFTP_test_rmdir_two_nested_dirs_dir2"
        self.sftp_client.connection.mkdir(f"{dir1}/{dir2}")
        self.assertTrue(self.sftp_client.connection.isdir(f"{dir1}/{dir2}"))

        # Remove nested directories
        self.sftp_client.rmdir([dir1])
        self.assertFalse(self.sftp_client.connection.isdir(dir1))

    def test_rmdir_multiple_nested_dirs(self):
        """Test rmdir command with multiple nested directories"""
        # Test the rmdir command with multiple nested directories to:
        #  confirm that rmdir will delete all the directories

        # Create root directory
        dir1 = "SFTP_test_rmdir_multiple_nested_dirs"
        self.sftp_client.connection.mkdir(dir1)
        self.assertTrue(self.sftp_client.connection.isdir(dir1))

        # Create directories inside the root
        for i in range(1,5):
            self.sftp_client.connection.makedirs(f"{dir1}/a/b/c/dir{i}")
            self.assertTrue(self.sftp_client.connection.isdir(f"{dir1}/a/b/c/dir{i}"))

        # Remove nested directories
        self.sftp_client.rmdir([dir1])
        self.assertFalse(self.sftp_client.connection.isdir(dir1))

    def test_rmdir_multiple_nested_dirs_and_files(self):
        """Test rmdir command with multiple nested directories"""
        # Test the rmdir command with multiple nested directories and files to:
        #  confirm that rmdir will delete all the files and directories

        # Create root directory
        dir1 = "SFTP_test_rmdir_multiple_nested_dirs_and_files"
        self.sftp_client.connection.mkdir(dir1)
        self.assertTrue(self.sftp_client.connection.isdir(dir1))

        # Create directories inside the root
        for i in range(1,5):
            self.sftp_client.connection.makedirs(f"{dir1}/a/b/c/dir{i}")
            self.assertTrue(self.sftp_client.connection.isdir(f"{dir1}/a/b/c/dir{i}"))

        # Add files to directory tree
        dirs = []
        self.sftp_client.connection.walktree(dir1, None, dirs.append, None)
        for dir in reversed(dirs):
            self.sftp_client.connection.execute(f"touch {dir}/test_file")
            self.assertTrue(self.sftp_client.connection.isfile(f"{dir}/test_file"))
        self.sftp_client.connection.execute(f"touch {dir1}/test_file")
        self.assertTrue(self.sftp_client.connection.isfile(f"{dir1}/test_file"))

        # Remove nested directories
        self.sftp_client.rmdir([dir1])
        self.assertFalse(self.sftp_client.connection.isdir(dir1))


class RmCommandTestCase(SFTPTestCase):
    """RmCommandTestCase class provides a unittest class used for the rm command"""

    def test_rm_zero_arg(self):
        """Test rm command with zero arguments"""
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.rm([])

    def test_rm_file_exists(self):
        """Test rm command with file 'filepath' being removed from current directory"""
        # Successful run of test will remove 'filepath' from current working directory
        filepath = self.test_file_name

        dir_files = self.sftp_client.ls([])
        self.assertFalse(filepath in dir_files)

        self.sftp_client.connection.open(filepath, 'w')
        dir_files = self.sftp_client.ls([])
        self.assertTrue(filepath in dir_files)

        self.sftp_client.connection.remove(filepath)
        dir_files = self.sftp_client.ls([])
        self.assertFalse(filepath in dir_files)

    def test_rm_file_nonexistent(self):
        """Test rm command against a file that does not exist in the remote path"""
        # Successful run of test will return an TypeError
        dir_files = self.sftp_client.ls([])
        filepath = self.test_file_name
        self.assertFalse(filepath in dir_files)
        with self.assertRaises(TypeError):
            self.sftp_client.rm(filepath)


class MkdirCommandTestCase(SFTPTestCase):
    """MkdirCommandTestCase class provides a unittest class used for testing the SFTP mkdir command"""

    def test_mkdir_zero_arg(self):
        """Test mkdir command with zero arguments"""
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.mkdir([])

    def test_mkdir_single_dir(self):
        """Test mkdir command with path 'dirname' being created in current directory"""
        # Successful run of test will have newly created directory in current remote directory
        dir_path = 'yes_I_want_fries_with_that'
        dir_files = self.sftp_client.ls([])
        self.assertFalse(dir_path in dir_files)
        self.sftp_client.mkdir([dir_path])
        dir_files = self.sftp_client.ls([])
        self.assertTrue(dir_path in dir_files)
        self.sftp_client.rmdir([dir_path])
        dir_files = self.sftp_client.ls([])
        self.assertNotIn(dir_path, dir_files)

    def test_mkdir_nested_dir(self):
        """Test mkdir command with path 'nested/dir/dir_name"""
        # Successful run of test will create nested directories in current remote directory
        full_path = "nested/dir_name"
        split_path = full_path.split("/")
        dir_files = self.sftp_client.ls([])
        self.assertFalse(split_path[0] in dir_files)
        self.sftp_client.mkdir([full_path])
        dir_files = self.sftp_client.ls([split_path[0]])
        self.assertIn(split_path[1], dir_files)
        self.sftp_client.rmdir([split_path[0]])
        dir_files = self.sftp_client.ls([])
        self.assertNotIn(split_path[0], dir_files)


class LogHistoryTestCase(SFTPTestCase):
    """LogHistoryTestCase class provides a unittest class used for testing the SFTP log_history decorator"""

    def setUp(self):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def tearDown(self):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def test_log_history_ls_no_arg(self):
        """Test log_history with zero arguments to ls"""
        self.sftp_client.ls([])
        file_text = ""
        with open(HISTORY_FILE, "r") as f:
            file_text = f.read()
        self.assertEqual(file_text, "ls\n")

    def test_log_history_ls_one_arg(self):
        """Test log_history with one arguments to ls"""
        self.sftp_client.ls(['Downloads'])
        file_text = ""
        with open(HISTORY_FILE, "r") as f:
            file_text = f.read()
        self.assertEqual(file_text, "ls Downloads\n")

    def test_log_history_multiple_commands(self):
        """Test log_history with every SFTP command"""
        dir_name = "test_log_history_multiple_commands"
        file_name = "file1.txt"
        self.sftp_client.ls([])
        self.sftp_client.ls(["Downloads"])
        self.sftp_client.mkdir([dir_name])
        self.sftp_client.chmod([dir_name, 777])
        open(file_name, "w")
        self.sftp_client.put([file_name])
        self.sftp_client.put(["-t", dir_name, file_name])
        self.sftp_client.connection.execute(f"touch {dir_name}/{file_name}")
        self.sftp_client.get([f"{dir_name}/{file_name}"])
        self.sftp_client.get([f"{dir_name}/{file_name}", f"~/Desktop/{file_name}"])
        self.sftp_client.rm([f"{dir_name}/{file_name}"])
        self.sftp_client.rm([file_name])
        self.sftp_client.connection.rmdir(f"{dir_name}")
        os.remove(file_name)
        os.remove(os.path.expanduser(f"~/Desktop/{file_name}"))
        os.remove(f"{DOWNLOADS_DIRECTORY}/{file_name}")

        file_text = ""
        expected = ("ls\n"
                   "ls Downloads\n"
                   f"mkdir {dir_name}\n"
                   f"chmod {dir_name} 777\n"
                   f"put {file_name}\n"
                   f"put -t {dir_name} {file_name}\n"
                   f"get {dir_name}/{file_name}\n"
                   f"get {dir_name}/{file_name} ~/Desktop/{file_name}\n"
                   f"rm {dir_name}/{file_name}\n"
                   f"rm {file_name}\n")
        with open(HISTORY_FILE, "r") as f:
            file_text = f.read()
        self.assertEqual(file_text, expected)


class HistoryCommandTestCase(SFTPTestCase):
    """HistoryCommandTestCase class provides a unittest class used for testing the SFTP history command"""

    def setUp(self):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def tearDown(self):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def test_history_ls_no_arg(self):
        """Test history command with zero arguments to ls"""
        self.sftp_client.ls([])
        command_history = self.sftp_client.history([])
        self.assertEqual(command_history, "ls")

    def test_history_ls_one_arg(self):
        """Test history command with one argument to ls"""
        self.sftp_client.ls(["Downloads"])
        command_history = self.sftp_client.history([])
        self.assertEqual(command_history, "ls Downloads")

    def test_history_multiple_commands(self):
        """Test history command with every SFTP command"""
        dir_name = "test_log_history_multiple_commands"
        file_name = "file2.txt"
        file_text = ("ls\n"
                   "ls Downloads\n"
                   f"mkdir {dir_name}\n"
                   f"chmod {dir_name} 777\n"
                   f"put {file_name}\n"
                   f"put -t {dir_name} {file_name}\n"
                   f"get {dir_name}/{file_name}\n"
                   f"get {dir_name}/{file_name} ~/Desktop/{file_name}\n"
                   f"rm {dir_name}/{file_name}\n"
                   f"rm {file_name}\n")

        with open(HISTORY_FILE, "w") as f:
            f.write(file_text)
        command_history = self.sftp_client.history([])
        self.assertEqual(command_history, file_text.strip())


class RenameLCommandTestCase(SFTPTestCase):
    def test_renamel_zero_arg(self):
        """Test renamel command with zero arguments"""
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.renamel([])

    def test_renamel_one_arg(self):
        """Test renamel command with one arguments"""
        # renamel command needs exactly two arguments
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.renamel(["abc"])

    def test_renamel_two_arg_no_such_local_file(self):
        """Test rename command with two arguments, but file is not in remote server"""
        # Successful run of test returns a IOError
        # Assume remote server doesn't have a directory named "abc"
        with self.assertRaises(IOError):
            self.sftp_client.renamel(["abc", "cba"])

    def test_renamel_two_arg(self):
        """Test renamel command with two arguments, but file is in remote server"""
        # Successful run of test will rename directory in current remote directory
        # Assuming you don't have a rename_test dir in remote server
        file_name = 'rename_test'
        rename_file = 'test_rename'
        dir_files = self.sftp_client.lsl([])
        self.assertFalse(file_name in dir_files)
        os.mkdir(file_name)
        dir_files = self.sftp_client.lsl([])
        self.assertTrue(file_name in dir_files)
        self.sftp_client.renamel([file_name, rename_file])
        dir_files = self.sftp_client.lsl([])
        self.assertTrue(rename_file in dir_files)
        os.rmdir(rename_file)
        dir_files = self.sftp_client.lsl([])
        self.assertFalse(rename_file in dir_files)

    def test_renamel_nested(self):
        """Test renamel command with path 'nested/dir/dir_name"""
        # Successful run of test will rename nested directories in current remote directory
        full_path = 'rename/dir_name'
        rename_full_path = 'rename/rename_dir'
        split_path = rename_full_path.split("/")
        os.makedirs(full_path)
        dir_files = self.sftp_client.lsl([])
        self.assertTrue('rename', dir_files)
        self.sftp_client.renamel([full_path, rename_full_path])
        dir_files = os.listdir(split_path[0])
        self.assertIn(split_path[1], dir_files)
        os.removedirs(rename_full_path)

    def test_renamel_three_arg(self):
        """Test renamel command with three arguments"""
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.renamel(['abc', 'bcc', 'ccc'])


class RenameCommandTestCase(SFTPTestCase):
    def test_rename_zero_arg(self):
        """Test rename command with zero arguments"""
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.rename([])

    def test_rename_one_arg(self):
        """Test rename command with one arguments"""
        # rename command needs exactly two arguments
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.rename(["abc"])

    def test_rename_two_arg_no_such_remote_file(self):
        """Test rename command with two arguments, but file is not in remote server"""
        # Successful run of test returns a IOError
        # Assume remote server doesn't have a directory named "abc"
        with self.assertRaises(IOError):
            self.sftp_client.rename(["abc", "cba"])

    def test_rename_two_arg(self):
        """Test rename command with two arguments, but file is in remote server"""
        # Successful run of test will rename directory in current remote directory
        # Assuming you don't have a rename_test dir in remote server
        file_name = 'rename_test'
        rename_file = 'test_rename'
        self.sftp_client.mkdir([file_name])
        self.sftp_client.rename([file_name, rename_file])
        dir_files = self.sftp_client.ls([])
        self.assertTrue(rename_file in dir_files)
        self.sftp_client.rmdir([rename_file])

    def test_rename_nested(self):
        """Test rename command with path 'nested/dir/dir_name"""
        # Successful run of test will rename nested directories in current remote directory
        full_path = 'rename/dir_name'
        rename_full_path = 'rename/rename_dir'
        split_path = rename_full_path.split("/")
        self.sftp_client.mkdir([full_path])
        self.sftp_client.rename([full_path, rename_full_path])
        dir_files = self.sftp_client.ls([split_path[0]])
        self.assertIn(split_path[1], dir_files)
        self.sftp_client.rmdir(['rename'])

    def test_rename_three_arg(self):
        """Test rename command with three arguments"""
        # Successful run of test returns a TypeError
        with self.assertRaises(TypeError):
            self.sftp_client.rename(['abc', 'bcc', 'ccc'])


class CopyCommandTestCase(SFTPTestCase):
    """CopyCommandTestCase class provides a unittest class used for testing the SFTP cp command"""
    def setUp(self):
        self.sftp_client.connection.execute('mkdir ' + self.test_dir_name)
        self.sftp_client.connection.execute('touch ' + self.test_file_name)
        self.sftp_client.connection.execute('touch ' + self.test_dir_name + '/testfile1')
        self.sftp_client.connection.execute('mkdir ' + self.test_dir_name + '/testdir')
        self.sftp_client.connection.execute('touch ' + self.test_dir_name + '/testdir/testfile2')
        self.sftp_client.connection.execute('mkdir empty')

    def tearDown(self):
        self.sftp_client.connection.execute('rm -r ' + self.test_dir_name + ' ' + self.test_dir_name + '-copy empty empty1')
        self.sftp_client.connection.execute('rm ' + self.test_file_name)

    def assertCopyExists(self, item, msg=None):
        # append the string '-copy' to the end of `item`, so that the super class'
        # assertExists() method can be used to confirm whether a copy of the test dir exists
        item_copy = re.sub(self.test_dir_name, self.test_dir_name + '-copy', item)
        return super(CopyCommandTestCase, self).assertExists(item_copy, msg)

    def assertNestedExists(self, item, msg=None):
        # prepend the string 'empty/' to the front of self.test_dir_name and `item`,
        # so that the super class' assertExists() method can be used to confirm whether
        # a copy of the test dir exists within the destination directory 'empty'
        item_copy = re.sub(self.test_dir_name, 'empty/' + self.test_dir_name, item)
        try:
            return super(CopyCommandTestCase, self).assertExists(item_copy, msg)
        except AssertionError as e:
            raise e

    def test_copy_zero_arg(self):
        """Test cp command with zero arguments"""
        # Test the cp command with zero arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.cp([])

    def test_copy_one_arg(self):
        """Test cp command with one argument"""
        # Test the cp command with one argument to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.cp(['0xdeadbeef'])

    def test_copy_three_arg(self):
        """Test cp command with three arguments"""
        # Test the cp command with three arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.cp(['0xdeadbeef', '0xdeadbeef', '0xdeadbeef'])

    def test_copy_invalid_src(self):
        """Test cp command with an invalid src argument"""
        # Test the cp command with an invalid src argument to:
        #  confirm that the test will fail with a IOError exception
        with self.assertRaises(IOError):
            self.sftp_client.cp(['0xdeadbeef', '0xdeadbeef'])

    def test_copy_invalid_dst(self):
        """Test cp command with an invalid dst argument"""
        # Test the cp command with an invalid dst argument (an existing file) to:
        #  confirm that the src directory exists;
        #  confirm that the test will fail with a IOError exception
        self.assertTrue(self.sftp_client.connection.exists(self.test_file_name))
        with self.assertRaises(IOError):
            self.sftp_client.cp([self.test_dir_name, self.test_file_name])

    def test_copy_empty_src(self):
        """Test cp command with an empty src folder"""
        # Test the cp command with an an empty src directory to:
        #  confirm that the src directory exists;
        #  confirm that the src directory is empty;
        #  confirm that the dst directory doesn't exist;
        #  confirm that the test will copy the empty directory to dst
        #  confirm that the dst directory exists after copying;
        #  confirm that the dst directory is empty;
        self.assertTrue(self.sftp_client.connection.exists('empty'))
        self.assertTrue(len(self.sftp_client.connection.listdir('empty')) == 0)
        self.assertFalse(self.sftp_client.connection.exists('empty1'))
        self.sftp_client.cp(['empty', 'empty1'])
        self.assertTrue(self.sftp_client.connection.exists('empty1'))
        self.assertTrue(len(self.sftp_client.connection.listdir('empty1')) == 0)

    def test_copy_valid_src(self):
        """Test cp command with valid src and dst arguments"""
        # Test the cp command with valid src and dst arguments to:
        #  confirm that the src directory exists;
        #  confirm that the dst directory does not exist;
        #  confirm that the copy operation will complete without exception;
        #  confirm that the contents of dst match src

        # confirm that src_dir exists, and is a directory
        self.assertTrue(self.sftp_client.connection.exists(self.test_dir_name))
        self.assertTrue(self.sftp_client.connection.isdir(self.test_dir_name))

        # confirm that the destination directory doesn't exist
        dst_d = self.test_dir_name + '-copy'
        self.assertFalse(self.sftp_client.connection.exists(dst_d))

        # perform the copy
        result = self.sftp_client.cp([self.test_dir_name, dst_d])
        self.assertIsNone(result)

        # confirm that the copy now exists
        self.assertTrue(self.sftp_client.connection.exists(dst_d))

        # confirm that each directory exists when walking the copied directory tree
        self.sftp_client.connection.walktree(self.test_dir_name, self.assertCopyExists, self.assertCopyExists, self.assertCopyExists)

        # confirm that after removing something from the copied directory tree,
        # that the assertCopyExists method actual fails
        self.sftp_client.connection.execute('rm -r "' + self.test_dir_name + '-copy/testdir"')
        with self.assertRaises(AssertionError):
            self.sftp_client.connection.walktree(self.test_dir_name, self.assertCopyExists, self.assertCopyExists, self.assertCopyExists)

    def test_copy_nested(self):
        """Test cp command with nested dst directory"""
        # Test the cp command with valid src and existing dst arguments to:
        #  confirm that the src directory exists;
        #  confirm that the dst directory exist;
        #  confirm that the copy operation will complete without exception;
        #  confirm that the contents of dst/src match src

        # confirm that src_dir exists, and is a directory
        self.assertTrue(self.sftp_client.connection.exists(self.test_dir_name))
        self.assertTrue(self.sftp_client.connection.isdir(self.test_dir_name))

        # confirm that the destination directory exists, and is a directory
        dst_d = 'empty'
        self.assertTrue(self.sftp_client.connection.exists(dst_d))
        self.assertTrue(self.sftp_client.connection.isdir(dst_d))

        # perform the copy
        result = self.sftp_client.cp([self.test_dir_name, dst_d])
        self.assertIsNone(result)

        # confirm that the copy now exists
        self.assertTrue(self.sftp_client.connection.exists(dst_d + '/' + self.test_dir_name))

        # confirm that each directory exists when walking the (nested) copied directory tree
        self.sftp_client.connection.walktree(self.test_dir_name, self.assertNestedExists, self.assertNestedExists, self.assertNestedExists)

        # confirm that after removing something from the copied directory tree,
        # that the assertNestedExists method actual fails
        self.sftp_client.connection.execute('rm -r empty/"' + self.test_dir_name + '/testdir"')
        with self.assertRaises(AssertionError):
            self.sftp_client.connection.walktree(self.test_dir_name, self.assertNestedExists, self.assertNestedExists, self.assertNestedExists)


class CopyRCommandTestCase(SFTPTestCase):
    """CopyRCommandTestCase class provides a unittest class used for testing the SFTP cp_r command"""
    def setUp(self):
        self.sftp_client.connection.execute('mkdir ' + self.test_dir_name)
        self.sftp_client.connection.execute('touch ' + self.test_file_name)
        self.sftp_client.connection.execute('touch ' + self.test_dir_name + '/testfile1')
        self.sftp_client.connection.execute('mkdir ' + self.test_dir_name + '/testdir')
        self.sftp_client.connection.execute('touch ' + self.test_dir_name + '/testdir/testfile2')
        self.sftp_client.connection.execute('mkdir empty')

    def tearDown(self):
        self.sftp_client.connection.execute('rm -r ' + self.test_dir_name + ' ' + self.test_dir_name + '-copy')
        self.sftp_client.connection.execute('rm ' + self.test_file_name)
        self.sftp_client.connection.execute('rm -r empty empty1')

    def assertCopyExists(self, item, msg=None):
        # append the string '-copy' to the end of `item`, so that the super class'
        # assertExists() method can be used to confirm whether a copy of the test dir exists
        item_copy = re.sub(self.test_dir_name, self.test_dir_name + '-copy', item)
        return super(CopyRCommandTestCase, self).assertExists(item_copy, msg)

    def assertNestedExists(self, item, msg=None):
        # prepend the string 'empty/' to the front of self.test_dir_name and `item`,
        # so that the super class' assertExists() method can be used to confirm whether
        # a copy of the test dir exists within the destination directory 'empty'
        item_copy = re.sub(self.test_dir_name, 'empty/' + self.test_dir_name, item)
        try:
            return super(CopyRCommandTestCase, self).assertExists(item_copy, msg)
        except AssertionError as e:
            raise e

    def test_copy_r_zero_arg(self):
        """Test cp_r command with zero arguments"""
        # Test the cp_r command with zero arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.cp_r([])

    def test_copy_r_one_arg(self):
        """Test cp_r command with one argument"""
        # Test the cp_r command with one argument to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.cp_r(['0xdeadbeef'])

    def test_copy_r_three_arg(self):
        """Test cp_r command with three arguments"""
        # Test the cp_r command with three arguments to:
        #  confirm that the test will fail with a TypeError exception
        with self.assertRaises(TypeError):
            self.sftp_client.cp_r(['0xdeadbeef', '0xdeadbeef', '0xdeadbeef'])

    def test_copy_r_invalid_src(self):
        """Test cp_r command with an invalid src argument"""
        # Test the cp_r command with an invalid src argument to:
        #  confirm that the test will fail with a IOError exception
        with self.assertRaises(IOError):
            self.sftp_client.cp_r(['0xdeadbeef', '0xdeadbeef'])

    def test_copy_r_invalid_dst(self):
        """Test cp_r command with an invalid dst argument"""
        # Test the cp_r command with an invalid dst argument (an existing file) to:
        #  confirm that the src directory exists;
        #  confirm that the test will fail with a IOError exception
        self.assertTrue(self.sftp_client.connection.exists(self.test_file_name))
        with self.assertRaises(IOError):
            self.sftp_client.cp_r([self.test_dir_name, self.test_file_name])

    def test_copy_r_empty_src(self):
        """Test cp_r command with an empty src folder"""
        # Test the cp_r command with an an empty src directory to:
        #  confirm that the src directory exists;
        #  confirm that the src directory is empty;
        #  confirm that the dst directory doesn't exist;
        #  confirm that the test will copy the empty directory to dst
        #  confirm that the dst directory exists after copying;
        #  confirm that the dst directory is empty;
        self.assertTrue(self.sftp_client.connection.exists('empty'))
        self.assertTrue(len(self.sftp_client.connection.listdir('empty')) == 0)
        self.assertFalse(self.sftp_client.connection.exists('empty1'))
        self.sftp_client.cp_r(['empty', 'empty1'])
        self.assertTrue(self.sftp_client.connection.exists('empty1'))
        self.assertTrue(len(self.sftp_client.connection.listdir('empty1')) == 0)

    def test_copy_r_valid_src(self):
        """Test cp_r command with valid src and dst arguments"""
        # Test the cp_r command with valid src and dst arguments to:
        #  confirm that the src directory exists;
        #  confirm that the dst directory does not exist;
        #  confirm that the copy operation will complete without exception;
        #  confirm that the contents of dst match src

        # confirm that src_dir exists, and is a directory
        self.assertTrue(self.sftp_client.connection.exists(self.test_dir_name))
        self.assertTrue(self.sftp_client.connection.isdir(self.test_dir_name))

        # confirm that the destination directory doesn't exist
        dst_d = self.test_dir_name + '-copy'
        self.assertFalse(self.sftp_client.connection.exists(dst_d))

        # perform the copy
        result = self.sftp_client.cp_r([self.test_dir_name, dst_d])
        self.assertIsNone(result)

        # confirm that the copy now exists
        self.assertTrue(self.sftp_client.connection.exists(dst_d))

        # confirm that each directory exists when walking the copied directory tree
        self.sftp_client.connection.walktree(self.test_dir_name, self.assertCopyExists, self.assertCopyExists, self.assertCopyExists)

        # confirm that after removing something from the copied directory tree,
        # that the assertCopyExists method actual fails
        self.sftp_client.connection.execute('rm -r "' + self.test_dir_name + '-copy/testdir"')
        with self.assertRaises(AssertionError):
            self.sftp_client.connection.walktree(self.test_dir_name, self.assertCopyExists, self.assertCopyExists, self.assertCopyExists)

    def test_copy_r_nested(self):
        """Test cp_r command with nested dst directory"""
        # Test the cp_r command with valid src and existing dst arguments to:
        #  confirm that the src directory exists;
        #  confirm that the dst directory exist;
        #  confirm that the copy operation will complete without exception;
        #  confirm that the contents of dst/src match src

        # confirm that src_dir exists, and is a directory
        self.assertTrue(self.sftp_client.connection.exists(self.test_dir_name))
        self.assertTrue(self.sftp_client.connection.isdir(self.test_dir_name))

        # confirm that the destination directory exists, and is a directory
        dst_d = 'empty'
        self.assertTrue(self.sftp_client.connection.exists(dst_d))
        self.assertTrue(self.sftp_client.connection.isdir(dst_d))

        # perform the copy
        result = self.sftp_client.cp_r([self.test_dir_name, dst_d])
        self.assertIsNone(result)

        # confirm that the copy now exists
        self.assertTrue(self.sftp_client.connection.exists(dst_d + '/' + self.test_dir_name))

        # confirm that each directory exists when walking the (nested) copied directory tree
        self.sftp_client.connection.walktree(self.test_dir_name, self.assertNestedExists, self.assertNestedExists, self.assertNestedExists)

        # confirm that after removing something from the copied directory tree,
        # that the assertNestedExists method actual fails
        self.sftp_client.connection.execute('rm -r empty/"' + self.test_dir_name + '/testdir"')
        with self.assertRaises(AssertionError):
            self.sftp_client.connection.walktree(self.test_dir_name, self.assertNestedExists, self.assertNestedExists, self.assertNestedExists)


class PutCommandTestCase(SFTPTestCase):
    def test_put_file_not_found(self):
        """Test put when called on a non-existant file/folder"""
        with self.assertRaises(FileNotFoundError):
            self.sftp_client.put(['0xdeadbeef'])

    def test_put_file(self):
        """Test putting a file"""
        open(self.test_file_name, 'w')
        self.sftp_client.put([self.test_file_name])
        result = self.sftp_client.ls([])
        self.assertIn(self.test_file_name, result)
        self.sftp_client.rm([self.test_file_name])
        os.remove(self.test_file_name)

    def test_put_file_target(self):
        test_folder = 'someTestFolder'
        test_file = 'someTestFile'
        remote = self.sftp_client.ls([])
        self.assertNotIn(test_folder, remote)
        open(test_file, 'w')
        self.sftp_client.put(['-t', test_folder, test_file])
        remote = self.sftp_client.ls([])
        self.assertIn(test_folder, remote)
        inner = self.sftp_client.ls([test_folder])
        self.assertIn(test_file, inner)
        self.sftp_client.rmdir([test_folder])
        os.remove(test_file)

class PwdlCommandTestCase(SFTPTestCase):
    """ Provides unittests for pwd local command """

    def test_pwdl_no_args(self):
        """ Tests pwdl command without args """
        path = self.sftp_client.pwdl
        self.assertIsNotNone(path)

    def test_pwdl_with_args(self):
        """ Tests pwdl command with args """
        with self.assertRaises(TypeError):
            self.sftp_client.pwdl("Fried-Chicken-Sundae")


class CdlCommandTestCase(SFTPTestCase):
    """ Provides unittests for the change (local) directory command """
    def test_no_args(self):
        """ Tests cdl with no arguments """
        with self.assertRaises(TypeError):
            self.sftp_client.cdl([])

    def test_multi_args(self):
        """ Tests cdl with multiple args """
        with self.assertRaises(TypeError):
            self.sftp_client.cdl(["sa sd"])

    def test_invalid_path(self):
        """ Tests cdl with invalid path """
        dir = 'why_would_you_have_a_folder_named_this'
        with self.assertRaises(TypeError):
            self.sftp_client.cdl([dir])

    def test_valid_path(self):
        """ Tests cdl with a valid path """
        new_dir = "aksughafsiug"
        os.mkdir(new_dir)
        self.sftp_client.cdl([new_dir])
        cur_path = self.sftp_client.pwdl([])
        self.assertTrue(new_dir in os.path.split(cur_path))
        self.sftp_client.cdl(['../'])
        shutil.rmtree(new_dir)
        self.assertTrue(new_dir not in self.sftp_client.lsl([]))


class CdCommandTestCase(SFTPTestCase):
    """ CdCommandTestCase class provides unittests for the cd (remote) command"""

    def test_cd_valid_path(self):
        """ Tests cd remote command against a valid directory path """
        dir_path = 'dunkelheit'
        self.sftp_client.mkdir([dir_path])
        self.sftp_client.cd([dir_path])
        cur_path = self.sftp_client.pwd([])
        self.assertTrue(dir_path in os.path.split(cur_path))
        self.sftp_client.cd(['../'])
        self.sftp_client.rmdir([dir_path])
        self.assertTrue(dir_path not in str(self.sftp_client.pwd([])))



    def test_cd_invalid_path(self):
        """ Tests cd remote command against an inavlid path """
        with self.assertRaises(TypeError):
            self.sftp_client.cd('afhsadfha')


    def test_cd_no_args(self):
        """ Tests cd remote command with no args """
        with self.assertRaises(TypeError):
            self.sftp_client.cd([])

    def test_cd_too_many_args(self):
        """ Tests cd remote command with too many args """
        with self.assertRaises(TypeError):
            self.sftp_client.cd("RIP Earth")


class PwdCommandTestCase(SFTPTestCase):
    """ PwdCommandTestCase class provides unittests for the pwd (remote) command """

    def test_pwd_no_args(self):
        """ Tests pwd command with no args (the correct number of args) """
        cur_path = self.sftp_client.pwd([])
        self.assertTrue(cur_path)


    def test_pwd_with_args(self):
        """ Tests pwd command with args """
        with self.assertRaises(TypeError):
            self.sftp_client.pwd(["Mustard"])

def suite():
    suite = unittest.TestSuite()

    suite.addTest(PlaintextAuthenticationTestCase('test_plaintext_auth'))
    suite.addTest(PublicKeyAuthenticationTestCase('test_public_key_auth'))

    suite.addTest(PutCommandTestCase('test_put_file_not_found'))
    suite.addTest(PutCommandTestCase('test_put_file_target'))
    suite.addTest(PutCommandTestCase('test_put_file'))

    suite.addTest(ListCommandTestCase('test_list_file'))
    suite.addTest(ListCommandTestCase('test_list_nonexistent'))
    suite.addTest(ListCommandTestCase('test_list_incorrect_args'))
    suite.addTest(ListCommandTestCase('test_list_zero_arg'))
    suite.addTest(ListCommandTestCase('test_list_one_arg'))

    suite.addTest(ChmodCommandTestCase('test_chmod_zero_arg'))
    suite.addTest(ChmodCommandTestCase('test_chmod_three_arg'))
    suite.addTest(ChmodCommandTestCase('test_chmod_invalid_path'))
    suite.addTest(ChmodCommandTestCase('test_chmod_invalid_mode'))
    suite.addTest(ChmodCommandTestCase('test_chmod_invalid_int_mode'))
    suite.addTest(ChmodCommandTestCase('test_chmod_mode_000'))
    suite.addTest(ChmodCommandTestCase('test_chmod_mode_755'))

    suite.addTest(RmCommandTestCase('test_rm_zero_arg'))
    suite.addTest(RmCommandTestCase('test_rm_file_exists'))
    suite.addTest(RmCommandTestCase('test_rm_file_nonexistent'))

    suite.addTest(MkdirCommandTestCase('test_mkdir_zero_arg'))
    suite.addTest(MkdirCommandTestCase('test_mkdir_single_dir'))
    suite.addTest(MkdirCommandTestCase('test_mkdir_nested_dir'))

    suite.addTest(RenameCommandTestCase('test_rename_zero_arg'))
    suite.addTest(RenameCommandTestCase('test_rename_one_arg'))
    suite.addTest(RenameCommandTestCase('test_rename_two_arg_no_such_remote_file'))
    suite.addTest(RenameCommandTestCase('test_rename_two_arg'))
    suite.addTest(RenameCommandTestCase('test_rename_nested'))
    suite.addTest(RenameCommandTestCase('test_rename_three_arg'))

    suite.addTest(RenameLCommandTestCase('test_renamel_zero_arg'))
    suite.addTest(RenameLCommandTestCase('test_renamel_one_arg'))
    suite.addTest(RenameLCommandTestCase('test_renamel_two_arg_no_such_local_file'))
    suite.addTest(RenameLCommandTestCase('test_renamel_two_arg'))
    suite.addTest(RenameLCommandTestCase('test_renamel_nested'))
    suite.addTest(RenameLCommandTestCase('test_renamel_three_arg'))


    suite.addTest(GetCommandTestCase('test_get_zero_arg'))
    suite.addTest(GetCommandTestCase('test_get_one_arg'))
    suite.addTest(GetCommandTestCase('test_get_one_arg_no_such_remote_file'))
    suite.addTest(GetCommandTestCase('test_get_two_arg'))
    suite.addTest(GetCommandTestCase('test_get_two_arg_no_such_remote_file'))
    suite.addTest(GetCommandTestCase('test_get_two_arg_no_such_localpath'))
    suite.addTest(GetCommandTestCase('test_get_three_arg'))

    suite.addTest(CopyCommandTestCase('test_copy_zero_arg'))
    suite.addTest(CopyCommandTestCase('test_copy_one_arg'))
    suite.addTest(CopyCommandTestCase('test_copy_three_arg'))
    suite.addTest(CopyCommandTestCase('test_copy_invalid_src'))
    suite.addTest(CopyCommandTestCase('test_copy_invalid_dst'))
    suite.addTest(CopyCommandTestCase('test_copy_valid_src'))
    suite.addTest(CopyCommandTestCase('test_copy_nested'))

    suite.addTest(CopyRCommandTestCase('test_copy_r_zero_arg'))
    suite.addTest(CopyRCommandTestCase('test_copy_r_one_arg'))
    suite.addTest(CopyRCommandTestCase('test_copy_r_three_arg'))
    suite.addTest(CopyRCommandTestCase('test_copy_r_invalid_src'))
    suite.addTest(CopyRCommandTestCase('test_copy_r_invalid_dst'))
    suite.addTest(CopyRCommandTestCase('test_copy_r_valid_src'))
    suite.addTest(CopyRCommandTestCase('test_copy_r_nested'))

    suite.addTest(RmdirCommandTestCase('test_rmdir_zero_arg'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_two_arg'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_no_such_dir'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_one_empty_dir'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_wrong_permissions'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_one_dir_one_file'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_one_dir_multiple_files'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_two_nested_dirs'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_multiple_nested_dirs'))
    suite.addTest(RmdirCommandTestCase('test_rmdir_multiple_nested_dirs_and_files'))

    suite.addTest(LogHistoryTestCase('test_log_history_ls_no_arg'))
    suite.addTest(LogHistoryTestCase('test_log_history_ls_one_arg'))
    suite.addTest(LogHistoryTestCase('test_log_history_multiple_commands'))

    suite.addTest(HistoryCommandTestCase('test_history_ls_no_arg'))
    suite.addTest(HistoryCommandTestCase('test_history_ls_one_arg'))
    suite.addTest(HistoryCommandTestCase('test_history_multiple_commands'))
    suite.addTest(CdCommandTestCase('test_cd_valid_path'))
    suite.addTest(CdCommandTestCase('test_cd_invalid_path'))
    suite.addTest(CdCommandTestCase('test_cd_no_args'))
    suite.addTest(CdCommandTestCase('test_cd_too_many_args'))

    suite.addTest(PwdCommandTestCase('test_pwd_no_args'))
    suite.addTest(PwdCommandTestCase('test_pwd_with_args'))

    suite.addTest(CdlCommandTestCase('test_no_args'))
    suite.addTest(CdlCommandTestCase('test_multi_args'))
    suite.addTest(CdlCommandTestCase('test_invalid_path'))
    suite.addTest(CdlCommandTestCase('test_valid_path'))

    suite.addTest(PwdlCommandTestCase('test_pwdl_no_args'))
    suite.addTest(PwdlCommandTestCase('test_pwdl_with_args'))

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
