# -*- coding: utf-8 -*-
#
# © 2013-2017 Krux Digital, Inc.
#

#
# Standard libraries
#
from __future__ import absolute_import

#
# Third party libraries
#
from argparse import ArgumentParser, _ArgumentGroup

#
# Internal libraries
#
from krux.wrapper import Wrapper
from krux.logging import LEVELS, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FACILITY
from krux.constants import (
    DEFAULT_STATSD_HOST,
    DEFAULT_STATSD_PORT,
    DEFAULT_STATSD_ENV,
    DEFAULT_LOCK_DIR,
)


def get_parser(
    logging=True,
    stats=True,
    lockfile=True,
    logging_stdout_default=True,
    *args,
    **kwargs
):
    # GOTCHA: KruxParser takes in a logger and a stats object. However, "stats" parameter is already defined
    #         as a boolean flag. Do not change the name of that parameter and break backward compatibility.
    # TODO: Update and clean up the parameter names so we can pass logger and stats into KruxParser.
    parser = KruxParser(ArgumentParser(*args, **kwargs))

    # standard logging arguments
    if logging:
        parser = add_logging_args(parser, logging_stdout_default)

    # standard stats arguments
    if stats:
        parser = add_stats_args(parser)

    # standard lockfile args
    if lockfile:
        parser = add_lockfile_args(parser)

    return parser


def add_logging_args(parser, stdout_default=True):
    """
    Add logging-related command-line arguments to the given parser.

    Logging arguments are added to the 'logging' argument group which is
    created if it doesn't already exist.

    :argument parser: parser instance to which the arguments will be added
    """
    group = get_group(parser, 'logging')

    group.add_argument(
        '--log-level',
        default=DEFAULT_LOG_LEVEL,
        #env_var='LOG_LEVEL',
        choices=LEVELS.keys(),
        help='Verbosity of logging. (default: %(default)s)'
    )
    group.add_argument(
        '--log-file',
        default=None,
        #env_var='LOG_FILE',
        help='Full-qualified path to the log file '
        '(default: %(default)s).'
    )

    group.add_argument(
        '--no-syslog-facility',
        dest='syslog_facility',
        action='store_const',
        default=DEFAULT_LOG_FACILITY,
        const=None,
        help='disable syslog facility',
    )
    group.add_argument(
        '--syslog-facility',
        default=DEFAULT_LOG_FACILITY,
        #env_var='SYSLOG_FACILITY',
        help='syslog facility to use '
        '(default: %(default)s).'
    )
    #
    # If logging to stdout is enabled (the default, defined by the log_to_stdout arg
    # in __init__(), we provide a --no-log-to-stdout cli arg to disable it.
    #
    # If our calling script or subclass chooses to disable stdout logging by default,
    # we instead provide a --log-to-stdout arg to enable it, for debugging etc.
    #
    # This is particularly useful for Icinga monitoring scripts, where we don't want
    # logging info to reach stdout during normal operation, because Icinga ingests
    # everything that's written there.
    #
    if stdout_default:
        group.add_argument(
            '--no-log-to-stdout',
            dest='log_to_stdout',
            default=True,
            action='store_false',

            help='Suppress logging to stdout/stderr '
            '(default: %(default)s).'
        )
    else:
        group.add_argument(
            '--log-to-stdout',
            default=False,
            action='store_true',
            help='Log to stdout/stderr -- useful for debugging! '
            '(default: %(default)s).'
        )

    return parser


def add_stats_args(parser):
    """
    Add stats-related command-line arguments to the given parser.

    :argument parser: parser instance to which the arguments will be added
    """
    group = get_group(parser, 'stats')

    group.add_argument(
        '--stats',
        default=False,
        action='store_true',
        help='Enable sending statistics to statsd. (default: %(default)s)'
    )
    group.add_argument(
        '--stats-host',
        default=DEFAULT_STATSD_HOST,
        help='Statsd host to send statistics to. (default: %(default)s)'
    )
    group.add_argument(
        '--stats-port',
        default=DEFAULT_STATSD_PORT,
        help='Statsd port to send statistics to. (default: %(default)s)'
    )
    group.add_argument(
        '--stats-environment',
        default=DEFAULT_STATSD_ENV,
        help='Statsd environment. (default: %(default)s)'
    )

    return parser


def add_lockfile_args(parser):
    group = get_group(parser, 'lockfile')

    group.add_argument(
        '--lock-dir',
        default=DEFAULT_LOCK_DIR,
        help='Dir where lock files are stored (default: %(default)s)'
    )

    return parser


def get_group(parser, group_name):
    """
    Return an argument group based on the group name.

    This will return an existing group if it exists, or create a new one.

    :argument parser: :py:class:`python3:argparse.ArgumentParser` to
                      add/retrieve the group to/from.

    :argument group_name: Name of the argument group to be created/returned.
    """

    # We don't want to add an additional group if there's already a 'logging'
    # group. Sadly, ArgumentParser doesn't provide an API for this, so we have
    # to be naughty and access a private variable.
    groups = [g.title for g in parser._action_groups]

    if group_name in groups:
        group = parser._action_groups[groups.index(group_name)]
    else:
        group = parser.add_argument_group(group_name)

    return group


class KruxParser(Wrapper):
    def add_argument_group(self, *args, **kwargs):
        group = KruxGroup(wrapped=_ArgumentGroup(self, *args, **kwargs), logger=self._logger, stats=self._stats)
        self._wrapped._action_groups.append(group)
        return group


class KruxGroup(Wrapper):
    def add_argument(self, *args, **kwargs):
        return self._wrapped.add_argument(*args, **kwargs)
