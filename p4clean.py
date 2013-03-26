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

__version__ = '0.0.1'


class P4CleanConfig(object):
    """Configurations for processing the p4 depot clean up process."""

    SECTION_NAME = 'p4clean'
    EXCLUSION_OPTION = 'exclusion'

    def __init__(self, path="", exclusion=""):
        self.logger = logging.getLogger()
        args_exclusion_list = exclusion.split(';')
        config_exclusion_list = []

        validated_path = self.validate_config_file_path(path)
        if validated_path is None:
            # config file sets by user can't be found.
            self.logger.error("Config file does'nt exist: %s", path)
            raise IOError

        config_exclusion_list = self.parse_config_file(validated_path)

        # chain args and config file exclusion lists
        exclusion_list = itertools.chain(args_exclusion_list,
                                         config_exclusion_list)
        exclusion_list = list(exclusion_list)
        self.exclusion_regex = self.compute_regex(exclusion_list)

    def compute_regex(self, exclusion_list):
        return r'|'.join([fnmatch.translate(x) for x in exclusion_list]) or r'$.'

    def is_excluded(self, filename):
        return re.match(self.exclusion_regex, filename)

    def validate_config_file_path(self, source_path):
        """ Construct and return a valid source_path for config file.
        None is returned if the file doesn't exist"""
        if source_path is "":
            # if no source_path provided, set current
            # working directory
            path = os.getcwd()
        elif not os.path.isabs(source_path):
            # make source_path absolute
            path = os.path.abspath(source_path)
        else:
            # normalize in other cases
            path = os.path.normpath(source_path)
        if os.path.isdir(path):
            # append config filename
            path = path + '/.p4clean'
        if not os.path.exists(path):
            return None
        return path

    def parse_config_file(self, path):
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


def delete_empty_folders(root):
    """Delete all empty folders under root (excluding root)"""
    for path, directories, files in os.walk(root, topdown=False):
        if not files and path is not root:
            try:
                print "deleting " + path
                os.rmdir(path)
            except OSError, e:
                if e.errno == errno.ENOTEMPTY:
                    pass


def get_perforce_status(path):
    old_path = os.getcwd()
    try:
        os.chdir(path)
        return getoutput("p4 status")
    except Exception:
        print "Unexpected error:", sys.exc_info()
        return None
    finally:
        os.chdir(old_path)


def compute_files_to_delete(config, status):
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


def delete_untracked_files(config, path):
    perforce_status = get_perforce_status(path)
    files_to_delete = compute_files_to_delete(config, perforce_status)
    delete_files(files_to_delete)


def main():
    # TODO:
    # make pip install work.
    # add good logs
    # test this thing on a real folder
    # add interactive validation for files to delete (e.g.
    #   /(D)elete/(A)dd all/(S)kip/)
    parser = argparse.ArgumentParser()
    parser.add_argument("--path",
                        default='.',
                        help="root path from which all child empty folders will be deleted")
    parser.add_argument("--exclude",
                        default='',
                        help="files exclusion pattern (e.g.: *.txt")
    args = parser.parse_args()

    config = P4CleanConfig(args.path, args.exclude)

    delete_untracked_files(config, args.path)

    delete_empty_folders(args.path)


if __name__ == "__main__":
    main()
