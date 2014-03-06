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
import subprocess
import re
import fnmatch
import ConfigParser
import logging
import platform

__version__ = '0.1.1'

# Use
logging.basicConfig(format='%(message)s')
logger = logging.getLogger('p4clean')


def shell_execute(command):
    """ Run a shell command

    :command: the shell command to run
    :returns: None if command fail else the command output

    """
    try:
        result = subprocess.check_output(command.split(),
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        # Do nothing, the error is already sent to stderr
        return None
    return result


class Perforce(object):
    """ Interface to Perforce."""

    def __init__(self):
        (version, root) = self.info()
        self.root = root

    @staticmethod
    def info():
        """ Return perforce version and root."""
        # get version
        try:
            info = shell_execute("p4 info")
        except Exception:
            logger.exception("Perforce is unavailable:")
            return (None, None)
        if not info:
            logger.error("Perforce is unavailable")
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

    def is_inside_workspace(self):
        """Return True if path inside current workspace."""
        where = shell_execute("p4 where")
        if where is None:
            return False
        return True

    def get_untracked_files(self, root):
        """ Return a list of untracked files at the 'root' path. """
        fstat = self._get_perforce_fstat(root)
        if not fstat:
            return []
        depot_files = []
        for line in fstat.splitlines():
            if line:
                depot_file = os.path.normpath(line.lstrip("... clientFile").strip())
                if platform.system() == 'Windows':
                    depot_file = depot_file.lower()
                depot_files.append(depot_file)
        local_files = []
        for path, directories, files in os.walk(root):
            for file in files:
                local_file = os.path.join(path, file)
                if platform.system() == 'Windows':
                    local_file = local_file.lower()
                local_files.append(local_file)
	    # os.walk() treats symlinks to directories as if they 
	    # are directories, but we need to treat them as files.
	    for directory in directories:
		local_file = os.path.join(path, directory)
		if os.path.islink(local_file):
		    if platform.system() == 'Windows':
			local_file = local_file.lower()
		    local_files.append(local_file)
		
        untracked_files = set(local_files) - set(depot_files)
        return list(untracked_files)

    def _get_perforce_fstat(self, root):
        """ Return Perforce status for all files under 'root' path. """
        result = ""
        # Get all file at current version synced by the client (-Rh)
        try:
            fstat = shell_execute("p4 fstat -Rh -T clientFile " + os.path.join(root, "..."))
            if fstat:
                result = result + fstat
            else:
                return None
        except Exception:
            logger.exception("Perforce is unavailable:")
            return None
        # Add all opened files. This will make sure file opened for add don't
        # get cleaned
        try:
            fstat = shell_execute("p4 fstat -Ro -T clientFile " + os.path.join(root, "..."))
            if fstat:
                result = result + fstat
            else:
                return None
        except Exception:
            logger.exception("Perforce is unavailable:")
            return None
        return result


class P4CleanConfig(object):
    """Configurations for processing the p4 depot clean up process."""

    SECTION_NAME = 'p4clean'
    CONFIG_FILENAME = '.p4clean'
    EXCLUSION_OPTION = 'exclude'

    def __init__(self, perforce_root, exclusion=None):
        """  """
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
            logger.error("Invalid p4clean config file: No section named \"%s\" found." % P4CleanConfig.SECTION_NAME)
            return []
        except ConfigParser.NoOptionError:
            logger.error("Invalid p4clean config file: No option named \"%s\" found." % P4CleanConfig.EXCLUSION_OPTION)
            return []


class P4Clean:
    def __init__(self):
        self.dry_run = False
        self.config = None
        self.perforce = Perforce()

    def run(self):
        """ Restore current working folder and subfolder to orginal state."""
        parser = argparse.ArgumentParser()
        parser.add_argument('-n', '--dry-run',
                            action='store_true',
                            help="print names of files and folders that would be deleted")
        parser.add_argument('-q', '--quiet',
                            action='store_true',
                            help="do not print names of deleted files and folders")
        parser.add_argument('-e', '--exclude',
                            default=None,
                            help="semicolon separated exclusion pattern (e.g.: *.txt;*.log;")
        parser.add_argument('-v', '--version',
                            action='version',
                            version="p4clean version %s" % __version__)
        args = parser.parse_args()

        self.dry_run = args.dry_run
        if args.quiet:
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)

        if not self.perforce.is_inside_workspace():
            logger.error("Nothing to clean: Current folder is not inside a Perforce workspace. Validate your perforce workspace with the command 'p4 where' or configure you command line workspace.")
            return

        self.config = P4CleanConfig(self.perforce.root, args.exclude)

        (deleted_files_count, file_error_msgs) = self.delete_untracked_files()

        (deleted_folders_count, folder_error_msgs) = self.delete_empty_folders()

        if self.dry_run:
            logger.info(80 * "-")
            logger.info("P4Clean dry run summary:")
            logger.info(80 * "-")
            logger.info("%d untracked files would be deleted." % deleted_files_count)
            logger.info("%d empty folders would be deleted." % deleted_folders_count)
        else:
            logger.info(80 * "-")
            logger.info("P4Clean summary:")
            logger.info(80 * "-")
            logger.info("%d untracked files deleted." % deleted_files_count)
            logger.info("%d empty folders deleted." % deleted_folders_count)
            if file_error_msgs:
                logger.error("%s files could not be deleted" % len(file_error_msgs))
                logger.error("\n".join(file_error_msgs))
            if folder_error_msgs:
                logger.error("%s empty folders could not be deleted" % len(folder_error_msgs))
                logger.error("\n".join(folder_error_msgs))

    def delete_empty_folders(self):
        """Delete all empty folders under root (excluding root)"""
        deleted_count = 0
        error_msgs = []
        root = os.getcwd()
        for path, directories, files in os.walk(root, topdown=False):
            if not files and path is not root:
                absolute_path = os.path.abspath(path)
                if not self.config.is_excluded(absolute_path):
                    if not os.listdir(absolute_path):
                        if self.dry_run:
                            logger.info("Would delete folder: '%s' " % absolute_path)
                            deleted_count = deleted_count + 1
                            continue
                        try:
                            os.rmdir(absolute_path)
                            logger.info("Deleted folder: '%s' " % absolute_path)
                            deleted_count = deleted_count + 1
                        except Exception:
                            error_msgs.append("Cannot delete empty folder (%s)" % sys.exc_info()[1])

        return deleted_count, error_msgs

    def delete_untracked_files(self):
        deleted_count = 0
        error_msgs = []
        for filename in self.perforce.get_untracked_files(os.getcwd()):
            if not self.config.is_excluded(filename):
                if self.dry_run:
                    logger.info("Would delete file: '%s' " % filename)
                    deleted_count = deleted_count + 1
                    continue
                try:
                    os.remove(filename)
                except:
                    if platform.system() == 'Windows':
                        try:
                            # Second try on Windows. Maybe the file was read
                            # only?
                            os.chmod(filename, stat.S_IWRITE)
                            os.remove(filename)
                        except:
                            error_msgs.append("Cannot delete file (%s)" % sys.exc_info()[1])
                            continue
                    else:
                        error_msgs.append("Cannot delete file (%s)" % sys.exc_info()[1])
                logger.info("Deleted file: '%s'" % filename)
                deleted_count = deleted_count + 1
        return deleted_count, error_msgs


def main():
    P4Clean().run()

if __name__ == "__main__":
    main()
