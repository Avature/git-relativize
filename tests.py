from __future__ import print_function

import os
import shutil
import tempfile

from hamcrest import assert_that, is_

from git_relativize import (relativize, execute, list_submodules, find_git_dir,
                            git_config_get)


def create_repo(name):
    path = os.path.join(tempfile.mkdtemp('git-relativize-tests'), name)
    os.mkdir(path)
    execute('git init'.split(), cwd=path)

    change = os.path.join(path, 'filename')
    with open(change, 'w') as stream:
        stream.write(name)

    execute(['git', 'add', change], cwd=path)
    execute('git commit -m Initial'.split(), cwd=path)

    return path


def create_repository():
    master_repo = create_repo('master')
    subrepo_names = ('first', 'second', 'third')
    subrepos = [create_repo(name) for name in subrepo_names]

    # Place subrepos in a subdirectory
    # This replicates iats environment with jscore/phpcore and others
    os.mkdir(os.path.join(master_repo, 'subrepos'))

    # Add submodules
    for name, path in zip(subrepo_names, subrepos):
        origin = 'file://' + path
        dest = os.path.join('subrepos', name)
        execute(['git', 'submodule', 'add', origin, dest], cwd=master_repo)

    # Initialize submodules
    execute('git submodule update --init'.split(), cwd=master_repo)

    return master_repo, subrepos


def get_worktree(path):
    config_path = os.path.join(path, 'config')
    return git_config_get(config_path, 'core.worktree')


def has_absolute_subrepo(path):
    return any(os.path.isabs(get_worktree(subrepo))
               for subrepo in list_submodules(find_git_dir(path)))


def assert_subrepos_relative(path):
    if has_absolute_subrepo(path):
        raise AssertionError('Repository has absolute subrepos')


class TestRun(object):
    def setup(self):
        self.repo, self.subrepos = create_repository()

    def teardown(self):
        for repo in [self.repo] + self.subrepos:
            shutil.rmtree(repo)

    def test_it_should_run_ok(self):
        result = relativize(self.repo)

        assert_that(result, is_(True))
        assert_subrepos_relative(self.repo)

    def test_subrepos_worktree_points_to_its_place(self):
        relativize(self.repo)

        for path in list_submodules(self.repo):
            name = os.path.basename(path)
            destination = os.path.join(self.repo, 'subrepos', name)
            worktree_abs = os.path.abspath(path, get_worktree(path))

            assert_that(destination, is_(worktree_abs))

    def test_subrepos_gitdir_file_points_to_git_directory(self):
        relativize(self.repo)

        for path in list_submodules(self.repo):
            name = os.path.basename(path)
            worktree = os.path.join(self.repo, 'subrepos', name)
            with open(os.path.join(worktree, '.git')) as stream:
                gitdir_rel = stream.read().split(':')[1].strip()
            gitdir_abs = os.path.abspath(os.path.join(worktree, gitdir_rel))

            assert_that(gitdir_abs, is_(path))
