P4clean
========
.. image:: https://travis-ci.org/okcompute/p4clean.png?branch=master
    :target: https://travis-ci.org/okcompute/p4clean
    :alt: Build status

About
-----
P4clean returns a folder tree inside a local Perfoce workspace to its original state by deleting untracked files and removing all empty folders. An exclusion list can be set so untracked development files are not deleted.

**Warning**: This tool is to be used only if you are confident untracked files can be deleted. Otherwise 'p4 reconcile' (Perforce 2012.1 and later) may be a better choice.

Requirements
------------
Perforce server and command line tools must be installed.

Installation
------------
From pip::

    $ pip install --upgrade p4clean

From easy_install::

    $ easy_install -ZU p4clean


Usage
-----
To clean current folder hiearchy ::

    $ p4clean

Options::

    Usage: p4clean [options]

    Clean Perfoce local workspace.

    Options:
      -n, --dry-run         Print names of files and folders that would be deleted
      -q, --quiet           Do not print names of deleted files and folders
      -e, --exclude         Semicolon separated list of file and folder patterns to be ignored from the clean-up.
      -v, --version         Show program's version number and exit
      -h, --help            Show this help message and exit

Config file
-----------

An optional p4clean config file can be used. Add a file named '.p4clean' anywhere
inside the local workspace (Suggested location for .p4clean config file is workspace root).
At launch, p4clean looks recursively up to the workspace root for this file.
If found, matching pattern files and directories are excluded from the clean-up.

p4clean config file example::

    [p4clean]
    exclude = *.log;*/.git*;

