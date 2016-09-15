import io
import re
from setuptools import setup


def get_version_from_debian_changelog():
    with io.open('debian/changelog', encoding='utf8') as stream:
        return re.search('\((.+)\)', next(stream)).group(1)


setup(
    name='git-relativize',
    version=get_version_from_debian_changelog(),
    author='Javier Santacruz',
    author_email='javier.santacruz@avature.net',
    py_modules=['git_relativize'],
    entry_points="""
    [console_scripts]
    git-relativize = git_relativize:main
    """
)
