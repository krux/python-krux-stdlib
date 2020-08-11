# Copyright 2013-2020 Salesforce.com, inc.

from __future__ import generator_stop
from setuptools import setup, find_packages
from krux import VERSION

# URL to the repository on Github.
REPO_URL = 'https://github.com/krux/python-krux-stdlib'

# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
# We use the version to construct the DOWNLOAD_URL.
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))

REQUIREMENTS = [
    'pystache',
    'kruxstatsd',
    'lockfile',
    ]
TEST_REQUIREMENTS = [
    'coverage',
    'mock',
    'mypy',
    'nose',
    'pylint',
    'pytest',
    'pytest-cov',
    'pytest-mypy',
    'pytest-pylint',
    'pytest-runner',
]

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
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'pystache',
        'kruxstatsd',
        'lockfile',
    ],
    setup_requires=[
        'pytest-cov',
        'pytest-mypy',
        'pytest-pylint',
        'pytest-runner',
    ],
    tests_require=[
        'coverage',
        'mock',
        'mypy',
        'nose',
        'pylint',
        'pytest',
    ],
    python_requires='>=3.6,<4',
)
