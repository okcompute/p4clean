P4clean
========

About
-----
P4clean is a small utility used to return a local Perfoce workspace to its original state. It deletes any files not found in the depot or not currently opened for add. This utility uses 'p4 status' under the hood to find untracked files. Empty folders are also deleted.

If you prefer to add files to changelist instead of deleting, use Perforce's 'p4 reconcile' command instead.

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
      --path                path onto which the cleanup will be processed


Exclusion config file::

A permanent exclusion config file can be associated with the workspace. Add a file named '.p4clean' at the root level of the local worspace. each time p4clean is run it will look for it. Files or directories matching the file patterns listed will be excluded from the tool.

p4clean exclusion file example:

*******

[p4clean]
exclusion = *.log;*.git/*;

*******
