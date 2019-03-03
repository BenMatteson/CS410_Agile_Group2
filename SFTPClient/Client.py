import logging
import paramiko
import pysftp
import ntpath
import os

from paramiko import ssh_exception
from functools import wraps
import tempfile
import shutil

DOWNLOADS_DIRECTORY = "downloads"
HISTORY_FILE = "command_history.txt"


class SFTP(object):
    def __init__(self, hostname, username, password=None, private_key_password=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key_password = private_key_password
        self.local_directory = os.path.expanduser('~')
        self.connection = self.initiate_connection()
        if not os.path.exists(DOWNLOADS_DIRECTORY):
            os.mkdir(DOWNLOADS_DIRECTORY)
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def is_connected(self):
        """Check the connection (using the listdir() method) to confirm that it's active."""
        return True if self.connection.listdir() else False

    def log_history(func):
        """A decorator function for logging command history each time a command is executed"""
        @wraps(func)
        def logged_func(self, args):
            if len(args) > 0:
                with open(HISTORY_FILE, "a") as f:
                    f.write(func.__name__ + " " + " ".join(str(arg) for arg in args) + "\n")
            else:
                with open(HISTORY_FILE, "a") as f:
                    f.write(func.__name__ + "\n")
            return func(self, args)
        return logged_func

    # region Commands Section
    def ping(self, _args):
        """Returns 'pong' if the connection is alive, else 'nothing happened'"""
        return "pong" if self.connection.listdir() else "nothing happened"

    def history(self, args):
        """Return the current session's command history"""
        if len(args) != 0:
            raise TypeError('history takes exactly zero arguments (' + str(len(args)) + ' given)')

        command_history = ""
        if os.path.isfile(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                command_history = f.read().strip()
        return command_history

    @log_history
    def ls(self, args):
        """List directory contents on the remote server"""
        results = None
        if len(args) is 0:
            results = self.connection.listdir()
        elif len(args) is 1:
            results = self.connection.listdir(args[0])
        else:
            raise TypeError("Usage: ls [<dir_path>]")
        return results

    @log_history
    def chmod(self, args):
        """Change or modify permissions of directories and files on the remote server

            Set the mode of a remotepath to mode, where mode is an integer representation
            of the octal mode to use.
        """
        if len(args) is 2:
            self.connection.chmod(args[0], int(args[1]))
        else:
            raise TypeError('"Usage: chmod <file/dir_path> <mode>"')

    @log_history
    def rmdir(self, args):
        """
        Recursively delete a directory and all it's files and subdirectories
        """
        if len(args) != 1:
            raise TypeError('rmdir() takes exactly one argument (' + str(len(args)) + ' given)')

        if self.connection.isdir(args[0]):
            dirs = []
            self.connection.walktree(args[0], self.connection.remove, dirs.append, self.connection.remove)
            for dir in reversed(dirs):
                self.connection.rmdir(dir)
            self.connection.rmdir(args[0])
        else:
            raise TypeError(f"Error: '{args[0]}' is not a directory")


    @log_history
    def rm(self, args):
        """
            Remove file from remote path given by argument. Arg may include path ('/').
        """
        if len(args) != 1:
            raise TypeError("Usage: rm <filename | path/to/filename>")
        else:
            if self.connection.isfile(args[0]):
                self.connection.remove(args[0])
            else:
                raise IOError(f"The remote path '{args[0]}' is not a file")

    @log_history
    def mkdir(self, args):
        """
            Creates directory on remote path passed as an argument. Directories
            are created with permissions 775.
        """
        if len(args) != 1:
            raise TypeError("Usage: mkdir <dirname | path/to/dirname>")
        else:
            if args[0].find('/') != -1:
                self.connection.makedirs(args[0], mode=775)
            else:
                self.connection.mkdir(args[0], mode=775)

    @log_history
    def get(self, args):
        """
        Downloads a remote file to the local machine. Given a single remotepath
        argument (arg[0]), the file is placed in the DOWNLOADS_DIRECTORY. If
        given a remotepath argument (arg[0]) and a localpath argument (arg[1]),
        the file is downloaded to the localpath.
        """
        if len(args) < 1 or len(args) > 2:
            raise TypeError("get() takes 1 or 2 arguments (" + str(len(args)) + " given)")

        # Check file exists or pysftp will create an empty file in the target directory
        if self.connection.isfile(args[0]):
            if len(args) is 1:
                head, tail = ntpath.split(args[0])
                remote_file = tail or ntpath.basename(head)
                localpath = os.path.join(DOWNLOADS_DIRECTORY, remote_file)
                self.connection.get(args[0], localpath)
            elif len(args) is 2:
                self.connection.get(args[0], os.path.expanduser(args[1]))
        else:
            raise IOError(f"The remote path '{args[0]}' is not a file")

    @log_history
    def put(self, args):
        """
        Send a file to the remote server.
        Supports local paths for files, but only the file is put.
        Filename and mtime are preserved.
        Allows use if '-t' flag to set remote path which will be used for any following files. if any directory
        does not exist, it is created.
        """
        target = None
        iter_args = iter(args)
        for arg in iter_args:
            arg = os.path.expanduser(arg)
            if arg == '-t':
                target = next(iter_args)
            elif os.path.isfile(arg):
                if target is not None:
                    try:
                        self.connection.mkdir(target)
                    except IOError:
                        pass  # already exists
                    self.connection.put(arg, target + '/' + os.path.basename(arg), preserve_mtime=True)
                else:
                    self.connection.put(arg, preserve_mtime=True)
            elif os.path.isdir(arg):
                raise IOError("Cannot put directories")

            else:
                raise FileNotFoundError("couldn't find the requested file")

    def rename(self, args):
        if len(args) is 2:
            self.connection.rename(args[0], args[1])
        else:
            raise TypeError('rename() takes exactly two arguments (' + str(len(args)) + ' given)')

    def cp(self, args):
        """Copy a remote directory from src to dst

            This version of the cp command performs an extremely inefficient copy, by
            first doing a get of the remote directory into a local temporary directory,
            and then doing a put of that directory back onto the remote server.

            This is a pure (S)FTP solution, which means that it does not require the ability to perform
            remote shell execution).
        """
        if len(args) is 2:
            if self.connection.exists(args[0]):
                if self.connection.exists(args[1]) and self.connection.isdir(args[1]):
                    # the remote destination directory exists - copy the source directory into that one
                    remote_d = os.path.join(args[1], os.path.basename(args[0]))
                    nest_d = True
                elif self.connection.exists(args[1]) and self.connection.isfile(args[1]):
                    # the remote destination is a file - bail
                    raise IOError('cp: ' + args[1] + ': file already exists')
                else:
                    # the remote destination doesn't exist - copy the source to that path
                    remote_d = args[1]
                    nest_d = None

                # setup local vars
                tmp_d = tempfile.gettempdir()
                local_d = os.path.join(tmp_d, os.path.basename(args[0]))
                moved_local_d = os.path.join(tmp_d, os.path.basename(remote_d))
                logging.debug('Copying ' + args[0] + ' to ' + remote_d + ' using tmp_d:' + tmp_d)
                try:
                    # setup local vars
                    tmp_d = tempfile.gettempdir()
                    local_d = os.path.join(tmp_d, os.path.basename(args[0]))
                    logging.debug('Copying ' + args[0] + ' to ' + remote_d + ' using tmp_d:' + tmp_d)

                    # get the contents of the remote directory into the temporary folder
                    if len(self.connection.listdir(args[0])) > 0:
                        # if the source folder is empty, paramiko (or pysftp?) will not actually do a get_r(),
                        # but still reports success. This is an issue, and is being addressed by creating that folder manually
                        logging.debug('Starting get...')
                        self.connection.get_r(args[0], tmp_d, preserve_mtime=True)
                        logging.debug('Copied ' + os.path.basename(args[0]) + ' to ' + tmp_d)
                    else:
                        logging.debug('Creating empty directory at: ' + os.path.join(tmp_d, args[0]) + '...')
                        os.mkdir(os.path.join(tmp_d, args[0]))

                    if nest_d:
                        # if the target directory exists, copy the source into the destination
                        moved_local_d = local_d
                    else:
                        # if the target directory doesn't exist, copy the source directory to that path
                        logging.debug('Moving ' + local_d + ' to: ' + moved_local_d + '...')
                        os.rename(local_d, os.path.join(tmp_d, moved_local_d))

                    # get the remote directory path so that it can be passed to put_r
                    cwd = self.connection.pwd
                    logging.debug('Remote working directory: ' + cwd)
                    remote_path = os.path.join(cwd, remote_d)

                    # create the remote directory (if it doesn't exist)
                    if not self.connection.exists(remote_path):
                        logging.debug('Creating remote directory: ' + remote_path + '...')
                        self.connection.mkdir(remote_path)

                    # put the contents ofthe temporary
                    logging.debug('Starting put of src: ' + os.path.join(tmp_d, os.path.basename(remote_d)) + ' dst: ' + remote_path)
                    self.connection.put_r(os.path.join(tmp_d, os.path.basename(remote_d)), remote_path, preserve_mtime=True)
                finally:
                    # cleanup the local temporary directories
                    logging.debug('Starting cleanup...')
                    if os.path.exists(moved_local_d):
                        shutil.rmtree(moved_local_d)
                    if os.path.exists(local_d):
                        shutil.rmtree(local_d)
            else:
               raise IOError('cp: ' + args[0] + ': No such file or directory')
        else:
            raise TypeError('Usage: cp <remote_source> <remote_destination>')

    def cp_r(self, args):
        """Copy a remote directory from src to dst via remote command execution

            This is the most efficient way to copy remote directories, but may
            require the ability to perform remote shell commands (i.e., it may
            not be compatible with chrooted SFTP sessions or (S)FTP servers running
            on a non-POSIX OS.
        """
        if len(args) is 2:
            if self.connection.exists(args[0]):
                if self.connection.exists(args[1]) and self.connection.isfile(args[1]):
                   raise IOError('cp_r: ' + args[1] + ': File exists')
                else:
                    self.connection.execute('cp -Rp ' + args[0] + ' ' + args[1])
            else:
               raise IOError('cp_r: ' + args[0] + ': No such file or directory')
        else:
            raise TypeError('cp_r() takes exactly two arguments (' + str(len(args)) + ' given)')
    # endregion

    def lsl(self, _args):
        '''It does list all files and directories in your local machine. It will start with local folder where the
         script exist'''
        return os.listdir(os.getcwd())

    def close(self, _args):
        try:
            self.connection.close()
        except Exception:
            pass
        exit()

    def pwdl(self, _args):
        """ Returns the present (local) working directory """
        if(_args):
            raise TypeError("Usage: pwd")
        else:
            return print(os.getcwd())

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass

    def initiate_connection(self):
        # Connect, checking hostkey or caching on first connect
        # Based off of this stackoverflow question:
        #     https://stackoverflow.com/questions/53666106/use-paramiko-autoaddpolicy-with-pysftp

        # configure pysftp CnOpts
        hostkeys = None
        cnopts = pysftp.CnOpts()  # loads hostkeys from known_hosts.ssh
        if cnopts.hostkeys.lookup(self.hostname) is None:
            logging.debug('Key for host: ' + self.hostname + ' was not found in known_hosts')
            hostkeys = cnopts.hostkeys
            cnopts.hostkeys = None

        args = {'host': self.hostname,
                'username': self.username,
                'cnopts': cnopts}

        # Determine what type of authentication to use based on parameters provided
        ssh_key = os.path.expanduser('~') + '/.ssh/id_rsa'
        if self.password is not None:
            logging.debug('Using plaintext authentication')
            args['password'] = self.password
        elif os.path.isfile(ssh_key):
            logging.debug('Got SSH key: ' + ssh_key)
            # the file at ~/.ssh/id_rsa exists - use it as the (default) private key
            args['private_key'] = ssh_key
            if self.private_key_password is not None:
                logging.debug('Using public key authentication with DER-encoded private key')
                args['private_key_pass'] = self.private_key_password
            else:
                logging.debug('Using public key authentication with plaintext private key')
        else:
            raise ssh_exception.BadAuthenticationType('No supported authentication methods available',
                                                      ['password', 'public_key'])

        # connect using the authentication type determined above
        logging.debug('Connecting using arguments: ' + str(args))
        try:
            connection = pysftp.Connection(**args)
        except paramiko.SSHException as e:
            logging.critical(e)
            raise

        # On first connect, Save the new hostkey to known_hosts
        if hostkeys is not None:
            logging.debug('Appending new hostkey for ' + self.hostname + ' to known_hosts, and writing to disk...')
            hostkeys.add(self.hostname, connection.remote_server_key.get_name(),
                         connection.remote_server_key)
            hostkeys.save(pysftp.helpers.known_hosts())

        return connection
