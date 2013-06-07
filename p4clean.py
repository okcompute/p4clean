#!/usr/bin/env python
#
# Copyright (C) 2013 Pascal Lalancette
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Clean up local Perforce workspace.
"""

import os
import stat
import sys
import argparse
import errno
import subprocess
import re
import fnmatch
import ConfigParser
import logging

__version__ = '0.0.7'


def shell_execute(command):
    """ Run a shell command

    :command: the shell command to run
    :returns: None if command fail else the command output

    """
    try:
        result = subprocess.check_output(command.split(), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        # Do nothing, the error is already sent to stderr
        return None
    return result


class Perforce(object):
    """ Encapsulate generic perforce commands."""

    def __new__(cls):
        (version, root) = Perforce.info()
        if version >= 2012:
            instance = super(Perforce, cls).__new__(Perforce2012, root)
        else:
            instance = super(Perforce, cls).__new__(cls, root)

        instance.root = root
        return instance

    def __init__(self):
        pass

    @staticmethod
    def info():
        """ Return perforce version and root."""
        # get version
        try:
            info = shell_execute("p4 info")
        except Exception:
            print "Perforce is unavailable:", sys.exc_info()
            return (None, None)
        if not info:
            print "Perforce is unavailable"
            return (None, None)
        root = None
        version = None
        info_lines = info.lower().split('\n')
        for information in info_lines:
            if information.startswith('client root:'):
                root = information[12:]
                # filter space, line feed and line return.
                root = root.strip(' /\r\n')
            elif information.startswith('server version:'):
                version = information[15:]
                version = version.split('/')[2]
                version = version.split('.')[0]
                version = int(version)
        return (version, root)

    def is_inside_perforce_workspace(self):
        """Return True if path inside current workspace."""
        where = shell_execute("p4 where")
        if where is None:
            return False
        return True

    def get_untracked_files(self, root):
        local_files = []
        for path, directories, files in os.walk(root):
            for file in files:
                local_files.append(os.path.join(path, file).lower())
        fstat = self._get_perforce_fstat(root)
        depot_files = []
        for line in fstat.splitlines():
            if line:
                depot_files.append(os.path.normpath(line.lstrip("... clientFile").strip().lower()))
        untracked_files = set(local_files) - set(depot_files)
        return list(untracked_files)

    def _get_perforce_fstat(self, root):
        # get version
        try:
            return shell_execute("p4 fstat -Rh -T clientFile " + root + "\\...")
        except Exception:
            print "Perforce is unavailable:", sys.exc_info()
            return None


class Perforce2012(Perforce):
    """Perforce 2012 and up command"""

    def __init__(self):
        super(Perforce2012, self).__init__()

    def get_untracked_files(self, root):
        """Return list of untracked files. """
        status = self._get_perforce_status(root)
        status_lines = status.split('\n')
        untracked_files = []
        for filename in status_lines:
            if re.match('.*reconcile to add.*', filename):
                filename = re.sub(r"\s-\s.*$", "", filename)
                filename = filename.strip()
                untracked_files.append(filename)
        return untracked_files

    def _get_perforce_status(self, path):
        """ Return the output of calling the command line 'p4 status'. """
        old_path = os.getcwd()
        try:
            os.chdir(path)
            return shell_execute("p4 status")
        except Exception:
            print "Unexpected error:", sys.exc_info()
            return None
        finally:
            os.chdir(old_path)


class P4CleanConfig(object):
    """Configurations for processing the p4 depot clean up process."""

    SECTION_NAME = 'p4clean'
    CONFIG_FILENAME = '.p4clean'
    EXCLUSION_OPTION = 'exclude'

    def __init__(self, perforce_root, exclusion=None):
        """  """
        self.logger = logging.getLogger()
        # Look for the .p4clean file.
        config_exclusion_list = []
        config_path = self.config_file_path(perforce_root)
        if config_path:
            config_exclusion_list = self.parse_config_file(config_path)

        args_exclusion_list = []
        if exclusion:
            args_exclusion_list = exclusion.split(';')

        # chain args and config file exclusion lists
        exclusion_list = args_exclusion_list + config_exclusion_list
        # Exlude p4clean config file (path for *nix + windows)
        exclusion_list.append('*/' + P4CleanConfig.CONFIG_FILENAME)
        exclusion_list.append('*\\' + P4CleanConfig.CONFIG_FILENAME)
        self.exclusion_regex = self.compute_regex(exclusion_list)

    def compute_regex(self, exclusion_list):
        return r'|'.join([fnmatch.translate(x) for x in exclusion_list]) or r'$.'

    def is_excluded(self, filename):
        return re.match(self.exclusion_regex, filename)

    def config_file_path(self, root):
        """ Return absolute config file path. Return None if non-existent."""
        path = os.getcwd()
        root = os.path.abspath(root)
        while True:
            config_file = os.path.join(path, '.p4clean')
            if os.path.exists(config_file):
                return config_file
            else:
                if path.lower() == root.lower() or path == '/':
                    return None
                else:
                    path = os.path.dirname(path)

    def parse_config_file(self, path):
        """ Return exclusion list from a config file. """
        try:
            config_file = open(path)
            config_file.close()
        except IOError:
            # No .p4clean find. That's okay.
            return []
        config = ConfigParser.RawConfigParser()
        try:
            config.read(path)
            exclusion_list = config.get(P4CleanConfig.SECTION_NAME,
                                        P4CleanConfig.EXCLUSION_OPTION)
            return exclusion_list.split(';')
        except ConfigParser.NoSectionError:
            print "Error: Invalid p4clean config file: No section named \"%s\" found." % \
                P4CleanConfig.SECTION_NAME
            return []
        except ConfigParser.NoOptionError:
            print "Error: Invalid p4clean config file: No option named \"%s\" found." % \
                P4CleanConfig.EXCLUSION_OPTION
            return []


class P4Clean:
    """ Restore current working folder and subfolder to orginal state."""
    def __init__(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("--exclude",
                            default=None,
                            help="semicolon separated exclusion pattern (e.g.: *.txt;*.log;")
        parser.add_argument('-V', '--version',
                            action='version',
                            version="p4clean version %s" % __version__)
        args = parser.parse_args()

        self.perforce = Perforce()

        if not self.perforce.is_inside_perforce_workspace():
            return

        self.config = P4CleanConfig(self.perforce.root, args.exclude)

        (deleted_files_count, deleted_error_count) = self.delete_untracked_files()
        deleted_folders_count = self.delete_empty_folders()

        print 80 * "-"
        print "P4Clean summary:"
        print 80 * "-"
        print "%d untracked files deleted." % deleted_files_count
        print "%d empty folders deleted." % deleted_folders_count
        if deleted_error_count > 0:
            print "%s files could not be deleted" % deleted_error_count

    def delete_empty_folders(self):
        """Delete all empty folders under root (excluding root)"""
        empty_folder_count = 0
        root = os.getcwd()
        for path, directories, files in os.walk(root, topdown=False):
            if not files and path is not root:
                absolute_path = os.path.abspath(path)
                if not self.config.is_excluded(absolute_path):
                    try:
                        os.rmdir(absolute_path)
                        print "Folder deleted: '%s' " % absolute_path
                        empty_folder_count = empty_folder_count + 1
                    except OSError, e:
                        if e.errno == errno.ENOTEMPTY:
                            pass
        return empty_folder_count

    def delete_untracked_files(self):
        deleted_count = 0
        error_count = 0
        for filename in self.perforce.get_untracked_files(os.getcwd()):
            if not self.config.is_excluded(filename):
                # Make sure the file is writable before deleting otherwise the
                # delete process fails
                os.chmod(filename, stat.S_IWRITE)
                try:
                    os.remove(filename)
                    print "Deleted file: '%s' " % filename
                    deleted_count = deleted_count + 1
                except:
                    print "Cannot delete file (%s)" % sys.exc_info()[1]
                    error_count = error_count + 1
        return (deleted_count, error_count)


def main():
    P4Clean()

if __name__ == "__main__":
    main()
