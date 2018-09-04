# -*- coding: utf-8 -*-
import os
import re
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand


def read_file(filename):
    """Open and a file, read it and return its contents."""
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path) as f:
        return f.read()


def get_metadata(init_file):
    """Read metadata from a given file and return a dictionary of them"""
    return dict(re.findall("__([a-z]+)__ = '([^']+)'", init_file))


class PyTest(TestCommand):

    """Command to run unit tests after in-place build."""

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = [
            '-sv',
            '--pep8',
            '--cov', 'flask_batch',
            '--cov-report', 'term-missing',
        ]
        self.test_suite = True

    def run_tests(self):
        # Importing here, `cause outside the eggs aren't loaded.
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


init_path = os.path.join('flask_batch', '__init__.py')
init_py = read_file(init_path)
metadata = get_metadata(init_py)

client_requires = [
    'requests'
]

setup(
    name='Flask-Batch',
    version=metadata['version'],
    author=metadata['author'],
    author_email=metadata['email'],
    url=metadata['url'],
    license=metadata['license'],
    long_description=read_file('README.rst'),
    packages=find_packages(include=('flask_batch*',)),
    install_requires=[
        "six",
        "werkzeug-raw",
        "flask",
    ],
    tests_require=[
        "mock",
        "pytest",
        "pytest-pep8",
        "pytest-flakes",
        "pytest-cov",
        "tox",
    ],
    extras_require={
        'client': client_requires
    },
    cmdclass={'test': PyTest},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
)
