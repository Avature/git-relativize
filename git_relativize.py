#!/usr/bin/env python
"""Fix absolute paths in git subrepos

When a repository with subrepos is cloned using a git version 1.7.9.*
absolute paths are generated pointing to the current subrepos directories.
Affected files are:

* .git/modules/NAME/config where core.worktree value is an absolute path to the
                           subrepo working tree directory.
* /submodule/worktree/.git where there is an absolute path to submodule git dir.

Both should be ported to be relative paths, which is now the default behaviour
in modern versions of git.

To do that, replace absolute paths with relative paths assuming the working
directory base is the same directory where the file is.
"""
import io
import os
import sys
import logging
import argparse
import subprocess


def relativize(path):
    """Fix absolute paths in git repositories"""
    path = os.path.abspath(os.path.expanduser(path))
    logging.info('Fixing repository at %s', path)

    git_dir = find_git_dir(path)
    if git_dir is None:
        return False

    logging.debug('Git repository found at %s', git_dir)

    for subpath in list_submodules(git_dir):
        name = os.path.basename(subpath)
        logging.info('Fixing submodule %s', name)
        logging.debug('Submodule %s path is %s', name, subpath)

        config_path = os.path.join(subpath, 'config')
        if not os.path.exists(config_path):
            logging.error('Could not find file: %s', config_path)
            return False

        fix_submodule_gitdir(config_path)
        fix_submodule_worktree(config_path)

    return True


def list_submodules(path):
    """Lists submodules within a given git dir"""
    submodules = [
        root for root, dirs, files
        in os.walk(os.path.join(path, 'modules'))
        if 'config' in files
    ]
    if submodules:
        logging.info('Found %d submodules: %s', len(submodules),
                      ', '.join(map(os.path.basename, submodules)))
        logging.debug('Found submodules at %s:\n\t%s',
                      path, '\n\t'.join(submodules))
    else:
        logging.info('No submodules')
    return submodules


def git_config_get(path, key):
    return execute_output(('git', 'config', '--file', path, '--get', key))


def git_config_set(path, key, value):
    execute(('git', 'config', '--file', path, '--replace-all', key, value))


def fix_submodule_worktree(path):
    """Fixes worktree in submodule config file"""
    logging.debug('Fixing config file %s', path)
    worktree = git_config_get(path, 'core.worktree')
    logging.debug('Found worktree %s in config file %s', worktree, path)

    if not os.path.isabs(worktree):
        logging.warning('No need to fix %s file as its worktree '
                        'its already a relative path: %s', path, worktree)
        return

    base = os.path.dirname(path)
    relative = os.path.relpath(worktree, base)
    logging.debug('Fixing absolute worktree path from %s to %s',
                  worktree, relative)

    git_config_set(path, 'core.worktree', relative)


def fix_submodule_gitdir(path):
    """Fixes gitdir file in submodule as from config file"""
    gitdir_path = os.path.dirname(path)
    worktree = git_config_get(path, 'core.worktree')
    logging.debug('Worktree is %s', worktree)
    if not os.path.isabs(worktree):
        worktree = os.path.abspath(os.path.join(gitdir_path, worktree))
        logging.debug('Calculated worktree path as %s', worktree)

    gitfile_path = os.path.join(worktree, '.git')
    logging.debug('The .git file should be at %s and point to %s',
                  gitfile_path, gitdir_path)

    if not os.path.exists(gitfile_path):
        logging.warning('No need to fix .git file as it does not exists at %s '
                        'Submodule might be not initialized.', gitfile_path)
        return

    relative = os.path.relpath(gitdir_path, worktree)
    logging.debug('Writing %s file with %s', gitfile_path, relative)
    with io.open(gitfile_path, 'w') as stream:
        stream.write(u'gitdir: ' + relative)


def find_git_dir(directory):
    """Finds git dir within given path"""
    path = directory
    if is_git_worktree(path):
        path = os.path.join(path, '.git')

    if is_git_dir(path):
        return path

    logging.error('Could not find .git repo in %s', path)


def is_git_worktree(path):
    command = 'git rev-parse --is-inside-work-tree'.split()
    return execute_output(command, cwd=path) == 'true'


def is_git_dir(path):
    command = 'git rev-parse --is-inside-git-dir'.split()
    return execute_output(command, cwd=path) == 'true'


def execute_output(command, **kwargs):
    ret, stdout, _ = execute(command, **kwargs)
    return stdout.strip()


def execute(command, fail=True, **kwargs):
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        if fail:
            logging.error('Command: %s failed with code %d\n'
                          'stdout:\n%s\n\nstderr:%s\n',
                          command, process.returncode, stdout, stderr)
            sys.exit(process.returncode)
        else:
            logging.warning('Command: %s failed with code %d',
                            command, process.returncode)

    return process.returncode, stdout, stderr


def parse_args():
    parser = argparse.ArgumentParser(
        description='Fix old git repos with absolute path for submodules'
    )
    parser.add_argument(
        '-v', '--verbosity',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Verbosity level default: INFO'
    )
    parser.add_argument(
        'paths',
        nargs='+',
        metavar='PATH',
        help='Path to repositories to be fixed'
    )
    return parser.parse_args()


def configure_logging(verbosity):
    logging.basicConfig(
        level=getattr(logging, verbosity),
        format='%(asctime)s %(levelname)s %(message)s'
    )


def main():
    args = parse_args()
    configure_logging(args.verbosity)

    error = False
    for path in args.paths:
        if not relativize(path):
            error = True
            logging.error('Could not fix %s', path)
        else:
            logging.debug('Fixed %s', path)

    sys.exit(2 if error else 0)


if __name__ == "__main__":
    main()
