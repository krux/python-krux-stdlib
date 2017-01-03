# -*- coding: utf-8 -*-
#
# © 2013-2015 Krux Digital, Inc.
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

REQUIREMENTS = ['pystache', 'Sphinx','kruxstatsd', 'argparse', 'tornado', 'simplejson', 'GitPython', 'lockfile']
if os.name == 'posix' and sys.version_info[0] < 3:
    # For Python 2.*, install the backported subprocess
    REQUIREMENTS.append('subprocess32')

setup(
    name='krux-stdlib',
    version=VERSION,
    author='Paul Lathrop',
    author_email='paul@krux.com',
    maintainer='Paul Lathrop',
    maintainer_email='paul@krux.com',
    description='Standard library of python modules used at Krux.',
    long_description="""
    Standard library of python modules used at Krux. These modules are written
    to make it easy to do things the Krux Way in your Python applications.
    """,
    url=REPO_URL,
    download_url=DOWNLOAD_URL,
    license='License :: OSI Approved :: MIT License',
    packages=find_packages(),
    install_requires=REQUIREMENTS,
    tests_require=[
        'coverage',
        'mock',
        'nose',
    ],
)
