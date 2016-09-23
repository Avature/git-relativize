git-relativize
==============

Fixes git repositories with absolute paths for submodules.

Usage
-----

Pass the path to one or more git repositories (or its .git directories).

    usage: git-relativize [-h] [-v {DEBUG,INFO,WARNING,ERROR}] PATH [PATH ...]

    Fix old git repos with absolute path for submodules

    positional arguments:
    PATH                  Path to repositories to be fixed

    optional arguments:
    -h, --help            show this help message and exit
    -v {DEBUG,INFO,WARNING,ERROR}, --verbosity {DEBUG,INFO,WARNING,ERROR}
                            Verbosity level default: INFO

The process will return with 0 when ok.  
The process will return with error code 1 when it fails performing an operation.  
The process witl return with error code 2 when it could not relativize some repositories.

Install
-------

For **Linux**:

Generate and install the debian package:

    dpkg-buildpackage -us -uc -b
    sudo dpkg -i ../git-relativize_*.deb

For **Mac**:

Install it via brew:

    brew install ./git-relativize/brew/git-relativize.rb

Submodules
----------

A git repository can make other repos to be part of it by declaring them as submodules.

eg:

    git submodule add git@../name  subrepos/name
    git submodule update --init

In this case, by default, the submodule has the *worktree* in `./subrepos/name`, its git repository
is placed in `.git/modules/subrepos/name`.

Configuration files are placed to locate each directory:

* In the subrepo *config file* at `.git/modules/subrepos/name/config` a `core.worktree` entry is
  added pointing to the worktree in `subrepos/name`.
* In the *worktree* A *.git* file is placed pointing to the submodule git repo
  `.git/modules/submodules/name`.

Problem
-------

The git version 1.7.9.* used to initialize submodules placing absolute paths in them.  
That causes a lot of trouble when moving repositories from one place to another,
or when mounting them into another filesystem.  

Fix
---

The fix rewrites those config files and converts absolute paths to relative paths, based on the
directory where the configuration file is placed.

Development
-----------

Create a virtualenv and install the app in dev mode:

    virtualenv env
    . env/bin/activate
    (env) pip install -e .

Testing
-------

Install tox and run tests for all environments with it:

    pip install tox
    tox

To run the tests, install the testing dependencies and run `nosetests`:

    (env) pip install -r dev-requirements.txt
    (env) nosetests
