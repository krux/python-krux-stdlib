# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
import sys
import os
from setuptools import setup, find_packages
from krux import VERSION


# URL to the repository on Github.
REPO_URL = 'https://github.com/krux/python-krux-stdlib'

# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
# We use the version to construct the DOWNLOAD_URL.
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))

REQUIREMENTS = ['pystache', 'kruxstatsd', 'argparse', 'lockfile', 'future']
if os.name == 'posix' and sys.version_info[0] < 3:
    # For Python 2.*, install the backported subprocess
    REQUIREMENTS.append('subprocess32')

TEST_REQUIREMENTS = ['coverage', 'mock', 'nose']

LINT_REQUIREMENTS = ['flake8']

setup(
    name='krux-stdlib',
    version=VERSION,
    author='Salesforce DMP Platform Engineering',
    author_email='krux-pe@salesforce.com',
    description='Standard library of python modules used at Krux.',
    long_description="""
    Standard library of python modules used at Krux. These modules are written
    to make it easy to do things the Krux Way in your Python applications.
    """,
    url=REPO_URL,
    download_url=DOWNLOAD_URL,
    license='License :: OSI Approved :: MIT License',
    packages=find_packages(exclude=['tests']),
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIREMENTS,
    extras_require={
        'dev': TEST_REQUIREMENTS + LINT_REQUIREMENTS,
    },
    python_requires='<4',
)
