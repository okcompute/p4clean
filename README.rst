P4clean
========

About
-----
P4clean returns a local Perfoce workspace to its original state. It deletes untracked files and removes all empty folders. 'p4 status' is used under the hood.

This tool is to be used only if you are certain untracked files can be deleted. If this is not the case, Perforce's 'p4 reconcile' may be more useful.

Requirements
------------

Perforce server and command line tools 2012.1 or higher must be installed.

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
      --exclusion           semicolon separated list of file patterns to exclud from the removal process.


Config file::

An optional p4clean config file can be associated with the workspace. Add a file named '.p4clean' at the root level of the local worspace. Each time p4clean is run it will look for it. A recursive lookup up to the root of the local workspace is done to find the file. This means you can call p4clean anywhere in the workspace folder tree. Files or directories matching the file patterns listed will be excluded from the tool.

p4clean config file example::

    [p4clean]
    exclusion = *.log;*/.git*;

