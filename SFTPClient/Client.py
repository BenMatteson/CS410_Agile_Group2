import logging
import paramiko
import pysftp
import ntpath
import os
from paramiko import ssh_exception
from functools import wraps

DOWNLOADS_DIRECTORY = "downloads"
HISTORY_FILE = "command_history.txt"


class SFTP(object):
    def __init__(self, hostname=None, username=None, password=None, private_key_password=None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key_password = private_key_password
        self.local_directory = os.path.expanduser('~')
        if self.hostname and self.username:
            # if a username + hostname is provided, there's a chance that we can connect
            self.connection = self.initiate_connection()
        else:
            # without a username + hostname, connection is impossible
            self.connection = None
        if not os.path.exists(DOWNLOADS_DIRECTORY):
            os.mkdir(DOWNLOADS_DIRECTORY)
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)

    def __str__(self):
        return ', '.join("%s" % str(item) for item in vars(self).items())

    def is_connected(self):
        """Check the connection (using the listdir() method) to confirm that it's active."""
        return self.connection is not None

    def log_history(func):
        @wraps(func)
        def logged_func(self, args):
            if (len(args) > 0):
                with open(HISTORY_FILE, "a") as f:
                    f.write(func.__name__ + " " + " ".join(str(arg) for arg in args) + "\n")
            else:
                with open(HISTORY_FILE, "a") as f:
                    f.write(func.__name__ + "\n")
            return func(self, args)
        return logged_func
        
    # region Commands Section
    def ping(self):
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
            raise TypeError('ls() takes exactly zero or one arguments (' + str(len(args)) + ' given)')
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
            raise TypeError('chmod() takes exactly two arguments (' + str(len(args)) + ' given)')
    
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
            raise TypeError("Usage: rm [filename | path/to/filename]")
        else:
            if self.connection.isfile(args[0]):
                self.connection.remove(args[0])
            else:
                raise TypeError("Usage: rm [filename | path/to/filename]")

    @log_history
    def mkdir(self, args):
        """
            Creates directory on remote path passed as an argument. Directories
            are created with permissions 775.
        """
        if len(args) != 1:
            raise TypeError("Usage: mkdir [dirname | path/to/dirname]")
        else:
            if args[0].find('/') != -1:
                self.connection.makedirs(args[0], mode = 775)
            else:
                self.connection.mkdir(args[0], mode = 775)

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
    
    @log_history
    def connect(self, args):
        """This command allows a user to interactively connect to an SFTP server"""
        logging.debug('connect() called with arguments: ' + str(arg) for arg in args)
        # clear out any exiting connect settings
        self.username = None
        self.hostname = None
        self.password = None
        self.private_key_password = None
        iter_args = iter(args)
        for arg in iter_args:
            if arg == '-U':
                self.username = next(iter_args)
            elif arg == '-H':
                self.hostname = next(iter_args)
            elif arg == '-P':
                self.password = next(iter_args)
            elif arg == '-p':
                self.private_key_password = next(iter_args)
            else:
                raise TypeError('connect() received an invalid argument: "' + str(arg) + '")')

        self.connection = self.initiate_connection()

    
    
    # endregion

    def lsl(self):
        '''It does list all files and directories in your local machine. It will start with local folder where the
         script exist'''
        return os.listdir(os.getcwd())

    def close(self):
        try:
            self.connection.close()
        except Exception:
            pass
        exit()

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass

    def initiate_connection(self):
        if not self.hostname:
            raise TypeError('initiate_connection(): hostname is required')
        elif not self.username:
            raise TypeError('initiate_connection(): username is required')

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
