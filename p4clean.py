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
import sys
import argparse
import errno
from commands import getoutput
import re
import fnmatch
import ConfigParser
import itertools
import logging

__version__ = '0.0.2'


class P4CleanConfig(object):
    """Configurations for processing the p4 depot clean up process."""

    SECTION_NAME = 'p4clean'
    CONFIG_FILENAME = '.p4clean'
    EXCLUSION_OPTION = 'exclusion'

    def __init__(self, perfoce_root, exclusion=None):
        """  """
        self.logger = logging.getLogger()
        # Look for the .p4clean file.
        config_exclusion_list = []
        config_path = self.config_file_path(perfoce_root, )
        if config_path:
            config_exclusion_list = self.parse_config_file(config_path)

        args_exclusion_list = []
        if exclusion:
            args_exclusion_list = exclusion.split(';')

        # chain args and config file exclusion lists
        exclusion_list = itertools.chain(args_exclusion_list,
                                         config_exclusion_list)
        exclusion_list = list(exclusion_list)
        exclusion_list.append(P4CleanConfig.CONFIG_FILENAME)
        self.exclusion_regex = self.compute_regex(exclusion_list)

    def compute_regex(self, exclusion_list):
        return r'|'.join([fnmatch.translate(x) for x in exclusion_list]) or r'$.'

    def is_excluded(self, filename):
        return re.match(self.exclusion_regex, filename)

    def config_file_path(self, root):
        """ Return absolute config file path. Return None if non-existent."""
        path = os.getcwd()
        while True:
            config_file = path + '/.p4clean'
            if os.path.exists(config_file):
                return config_file
            else:
                if path is root:
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


def delete_empty_folders(config, root):
    """Delete all empty folders under root (excluding root)"""
    empty_folder_count = 0
    for path, directories, files in os.walk(root, topdown=False):
        if not files and path is not root:
            absolute_path = os.path.abspath(path)
            if not config.is_excluded(absolute_path):
                try:
                    os.rmdir(absolute_path)
                    print "Folder '%s deleted'" % absolute_path
                    empty_folder_count = empty_folder_count + 1
                except OSError, e:
                    if e.errno == errno.ENOTEMPTY:
                        pass
    print "%d empty folders deleted." % empty_folder_count


def is_inside_perforce_workspace():
    """Return True if path inside current workspace."""
    try:
        where = getoutput("p4 where")
    except Exception:
        print "Perforce unavailable:", sys.exc_info()
        return False
    if re.match(".*is not under client's root.*", where):
        print "Path '%s' is not under Perforce client's root" % os.getcwd()
        return False
    return True


def get_perforce_root():
    """ Return the perforce root. """
    try:
        info = getoutput("p4 info")
    except Exception:
        print "Perforce is unavailable:", sys.exc_info()
        return None
    info_lines = info.split('\n')
    for information in info_lines:
        if information.startswith('Client root:'):
            root = information[12:]
            root = root.strip(' /')
            return root
    print "Invalid 'p4 info' result"
    return None


def get_perforce_status(path):
    """ Return the output of calling the command line 'p4 status'. """
    old_path = os.getcwd()
    try:
        os.chdir(path)
        return getoutput("p4 status")
    except Exception:
        print "Unexpected error:", sys.exc_info()
        return None
    finally:
        os.chdir(old_path)


def compute_files_to_delete(status, config):
    """ Parse the perforce status and return a list of files to delete. """
    status_lines = status.split('\n')
    files_to_delete = []
    for filename in status_lines:
        if re.match('.*reconcile to add.*', filename):
            filename = re.sub(r"\s-\s.*$", "", filename)
            filename = filename.strip()
            if not config.is_excluded(filename):
                files_to_delete.append(filename)
    return files_to_delete


def delete_files(files_list):
    for filename in files_list:
        os.remove(filename)
        print "File '%s deleted'" % filename


def delete_untracked_files(config, path):
    perforce_status = get_perforce_status(path)
    files_to_delete = compute_files_to_delete(perforce_status, config)
    delete_files(files_to_delete)
    print "%d files deleted." % len(files_to_delete)


def main():

    if not is_inside_perforce_workspace():
        return

    parser = argparse.ArgumentParser()
    parser.add_argument("--exclude",
                        default=None,
                        help="semicolon separated exclusion pattern (e.g.: *.txt;*.log;")
    args = parser.parse_args()

    config = P4CleanConfig(get_perforce_root(), args.exclude)

    delete_untracked_files(config, ".")
    delete_empty_folders(config, ".")


if __name__ == "__main__":
    main()
