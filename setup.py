# -*- coding: utf-8 -*-
#
# © 2013, 2014 Krux Digital, Inc.
#
from setuptools import setup, find_packages


# We use the version to construct the DOWNLOAD_URL.
VERSION      = '0.8.1'

# URL to the repository on Github.
REPO_URL     = 'https://github.com/krux/python-krux-stdlib'

# Github will generate a tarball as long as you tag your releases, so don't
# forget to tag!
DOWNLOAD_URL = ''.join((REPO_URL, '/tarball/release/', VERSION))


setup(
    name             = 'krux-stdlib',
    version          = VERSION,
    author           = 'Paul Lathrop',
    author_email     = 'paul@krux.com',
    maintainer       = 'Paul Lathrop',
    maintainer_email = 'paul@krux.com',
    description      = 'Standard library of python modules used at Krux.',
    long_description = """
    Standard library of python modules used at Krux. These modules are written
    to make it easy to do things the Krux Way in your Python applications.
    """,
    url              = REPO_URL,
    download_url     = DOWNLOAD_URL,
    license          = 'License :: OSI Approved :: MIT License',
    packages         = find_packages(),
    install_requires = [
        'Sphinx',
        'Jinja2',
        'Pygments',
        'docutils',
        'kruxstatsd',
        'statsd',
        'argparse',
        'GitPython',
        'simplejson',
        'tornado',
        'lockfile',
        'pygerduty',
        'async',
        'fudge',
        'gitdb',
        'smmap',
    ],
    tests_require = [
        'coverage',
        'mock',
        'nose',
    ]
)
