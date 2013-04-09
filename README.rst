P4clean
========

About
-----
P4clean returns a folder tree inside a local Perfoce workspace to its original state by deleting untracked files and removing all empty folders.

Warning: This tool is to be used only if you are confident untracked files can be deleted. Otherwise Perforce's 'p4 reconcile' may be a better choice.

Requirements
------------
Since 'p4 status' is used under the hood, Perforce server and command line tools 2012.1 or higher must be installed.

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
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      --exclude           semicolon separated list of file and folder patterns to be ignored from the clean-up.


Config file::

An optional p4clean config file can be used. Add a file named '.p4clean' anywhere inside the local workspace. At launch, p4clean looks recursively up to the workspace root for this file. If found, matching pattern files and directories are excluded from the clean-up. 

p4clean config file example::

    [p4clean]
    exclude = *.log;*/.git*;

