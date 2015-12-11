# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
This module adds tornado arguments to the base list of arguments
as provided by :py:mod:`cli <krux.cli>`.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import

######################
# Internal Libraries #
######################
from krux.cli import get_group

import krux.cli


#############
# Constants #
#############
DEFAULT_PORT = 8080
DEFAULT_ADDRESS = '0.0.0.0'
DEFAULT_BLOCKING_LOG_THRESHOLD = 5    # seconds


def add_tornado_args(parser):
    """
    Add tornado-related command-line arguments to the given parser.

    :argument object parser: :py:class:`ArgumentParser
                             <python3:argparse.ArgumentParser>` instance to
                             which the arguments will be added.
    """

    group = get_group(parser, 'tornado')

    group.add_argument(
        '--address',
        default=DEFAULT_ADDRESS,
        help='The IP address the application will bind to. '
        '(default: %(default)s)'
    )

    group.add_argument(
        '--http-port',
        default=DEFAULT_PORT,
        type=int,
        help='The TCP port the application will listen on for HTTP '
        'connections. (default: %(default)s)'
    )

    group.add_argument(
        '--blocking-log-threshold',
        default=DEFAULT_BLOCKING_LOG_THRESHOLD,
        type=int,
        help='The IOLoops blocking log treshold. '
        '(default: %(default)s)'
    )

    group.add_argument(
        '--development',
        default=False,
        action='store_true',
        help='Automatically reload application when source files change.'
    )

    return parser


def get_parser(**kwargs):
    """
    Wraps :py:func:`krux.cli.get_parser` and adds arguments as provided by
    :py:func:`add_tornado_args`.

    Keyword arguments are passed to :py:func:`krux.cli.get_parser`.
    """
    return add_tornado_args(krux.cli.get_parser(**kwargs))
