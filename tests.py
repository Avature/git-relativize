from __future__ import print_function

import os
import shutil
import tempfile

from hamcrest import assert_that, is_, has_length

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


def submodule_update(path):
    execute('git submodule update --init'.split(), cwd=path)


def add_subrepo(master, origin, dest):
    origin = 'file://' + origin
    execute(['git', 'submodule', 'add', origin, dest], cwd=master)
    submodule_update(master)


def create_repository(name):
    master_repo = create_repo(name)
    subrepo_names = ('first', 'second', 'third')
    subrepos = [create_repo(n) for n in subrepo_names]

    # Place subrepos in a subdirectory
    # This replicates iats environment with jscore/phpcore and others
    os.mkdir(os.path.join(master_repo, 'subrepos'))

    # Add submodules
    for subname, path in zip(subrepo_names, subrepos):
        add_subrepo(master_repo, path, os.path.join('subrepos', subname))

    execute('git commit -am Submodules'.split(), cwd=master_repo)

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
        self.repo, self.subrepos = create_repository('master')

    def teardown(self):
        for repo in [self.repo] + self.subrepos:
            shutil.rmtree(repo)

    def test_it_should_run_ok(self):
        result = relativize(self.repo)

        assert_that(result, is_(True))
        assert_subrepos_relative(self.repo)

    def test_list_subrepos_must_find_subrepos(self):
        subrepos = list_submodules(find_git_dir(self.repo))

        assert_that(subrepos, has_length(3))

    def assert_submodule_config_is_fixed(self, path, worktree=None):
        name = os.path.basename(path)
        destination = worktree or os.path.join(self.repo, 'subrepos', name)
        worktree_abs = os.path.abspath(os.path.join(path, get_worktree(path)))

        assert_that(destination, is_(worktree_abs))

    def test_subrepos_worktree_points_to_its_place(self):
        relativize(self.repo)

        for path in list_submodules(find_git_dir(self.repo)):
            self.assert_submodule_config_is_fixed(path)

    def assert_submodule_gitfile_is_fixed(self, path, worktree=None):
        name = os.path.basename(path)
        worktree = worktree or os.path.join(self.repo, 'subrepos', name)
        with open(os.path.join(worktree, '.git')) as stream:
            gitdir_rel = stream.read().split(':')[1].strip()
        gitdir_abs = os.path.abspath(os.path.join(worktree, gitdir_rel))

        assert_that(gitdir_abs, is_(path))

    def test_subrepos_gitdir_file_points_to_git_directory(self):
        relativize(self.repo)

        for path in list_submodules(find_git_dir(self.repo)):
            self.assert_submodule_gitfile_is_fixed(path)

    def test_list_subrepos_must_find_subrepos_in_different_locations(self):
        # Create a repo with subrepos instead or master repo
        subrepo_path, _ = create_repository('submaster')
        add_subrepo(self.repo, subrepo_path, 'sub_master')

        subrepos = list_submodules(find_git_dir(self.repo))

        assert_that(subrepos, has_length(4))

    def test_subrepos_get_fixed_recursively(self):
        # Create a repo with subrepos instead or master repo
        origin, _ = create_repository('submaster')
        add_subrepo(self.repo, origin, 'sub_master')
        subrepo_path = os.path.join(self.repo, '.git/modules', 'sub_master')

        # Initialize subsubrepositories
        subrepo_worktree = os.path.join(self.repo, 'sub_master')
        submodule_update(subrepo_worktree)

        relativize(self.repo)

        subsubmodules = list_submodules(subrepo_path)
        assert_that(subsubmodules, has_length(3))

        for path in subsubmodules:
            name = os.path.basename(path)
            worktree = os.path.join(subrepo_worktree, 'subrepos', name)
            self.assert_submodule_config_is_fixed(path, worktree)
            self.assert_submodule_gitfile_is_fixed(path, worktree)
