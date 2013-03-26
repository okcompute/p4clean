P4clean
========

About
-----
P4clean is a small utility to clean up your local workspace. Working with Perforce, your local folder can get messed up with log files, empty folders, etc. This utility will restore your local workspace as it should be after a clean get latest. This script should be faster then deleting all local files and folders and doing a "force" get latest revision.


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

    Usage: autopep8 [options] [filename [filename ...]]

    Clean Perfoce local workspace.

    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
