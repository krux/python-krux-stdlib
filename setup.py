# -*- coding: utf-8 -*-
#
# © 2013-2015 Krux Digital, Inc.
#
from setuptools import setup, find_packages


# We use the version to construct the DOWNLOAD_URL.
VERSION = '2.4.0'

# URL to the repository on Github.
REPO_URL = 'https://github.com/krux/python-krux-stdlib'

# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))


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
    install_requires=[
        'pystache==0.5.4',
        'Sphinx==1.4.6',
        'kruxstatsd==0.3.0',
        'argparse==1.4.0',
        'tornado==3.0.1',
        'simplejson==3.8.2',
        'GitPython==2.0.8',
        'lockfile==0.12.2',
        'subprocess32==3.2.7',
    ],
    tests_require=[
        'coverage==4.2',
        'mock==1.1.2',
        'nose==1.3.7',
    ],
)
