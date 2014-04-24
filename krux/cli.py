# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
This module provides tools for handling command-line arguments for a Krux
application.

Krux applications use :py:mod:`python3:argparse` for parsing command-line
options. The ``add_*_args`` functions in this module all expect to be called
with an instance of :py:class:`python3:argparse.ArgumentParser`, a subclass,
or an object that follows the same interface.

:py:mod:`python3:argparse` is part of the standard library in Python 3.x, but
Krux uses Python 2.6, so you will need to add it to your
:file:`requirements.pip` file::

    argparse==1.2.1

Usage::

        from krux.cli import get_parser, Application


        if __name__ == '__main__':

            ### functional
            parser = get_parser(description = 'My Krux CLI App')

            ### OO
            app     = Application(name = 'My Krux CLI App')
            parser  = app.parser

"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from functools import partial
from sys import exit

import os.path

#########################
# Third Party Libraries #
#########################
from argparse import ArgumentParser
from lockfile import FileLock

######################
# Internal Libraries #
######################
from krux.logging import LEVELS
from krux.constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_STATSD_HOST,
    DEFAULT_STATSD_PORT,
    DEFAULT_STATSD_ENV,
    DEFAULT_LOCK_DIR,
    DEFAULT_LOCK_TIMEOUT,
)

import krux.stats
import krux.logging


######################
### Object interface #
######################

class ApplicationError(StandardError):
    pass

class CriticalApplicationError(StandardError):
    """
    This error is only raised if the application is expected to exit.
    It should never be caught.
    """
    pass

class Application(object):
    """
    Krux base class for CLI applications

    :argument name: name of your CLI application
    """
    def __init__(self, name, parser=None, logger=None, lockfile=False):
        """
        Wraps :py:class:`object` and sets up CLI argument parsing, stats and
        logging.

        :keyword string name: name of the application. Should be unique to Krux
        (required)

        :keyword parser: The CLI parser. Defaults to
        :py:func:`cli.get_parser <krux.cli.get_parser>`
        """

        ### note our name
        self.name = name

        ### get a CLI parser
        self.parser = parser or krux.cli.get_parser(description=name)

        ### get more arguments, if needed
        self.add_cli_arguments(self.parser)

        ### and parse them
        self.args = self.parser.parse_args()

        ### get a logger - is there a way to to have logger be relative to the
        ### invocation of the log call?
        self.logger = logger or krux.logging.get_logger(
            name, level=self.args.log_level
        )

        ### get a stats object - any arguments are handled via the CLI
        ### pass '--stats' to enable stats using defaults (see krux.cli)
        self.stats = krux.stats.get_stats(
            client=getattr(self.args, 'stats', None),
            prefix='cli.%s' % name,
            env=getattr(self.args, 'stats_environment', None),
            host=getattr(self.args, 'stats_host', None),
            port=getattr(self.args, 'stats_port', None),
        )

        ### Exit hooks are run when the exit() method is called.
        self._exit_hooks = []

        ### Do you want an exclusive lock for this application?
        ### This can be done later as well, with an explicit path
        self.lockfile = False

        if lockfile:
            self.acquire_lock(lockfile)

    def acquire_lock(self, lockfile=True):
        ### Did you just tell us to use a lock, or did you give us a location?
        _lockfile = lockfile == True \
            and os.path.join( DEFAULT_LOCK_DIR, self.name ) \
            or lockfile

        ### this will throw an execption if anything goes wrong
        self.lockfile = FileLock(_lockfile)
        self.lockfile.acquire( timeout = DEFAULT_LOCK_TIMEOUT )

        self.logger.debug("Acquired lock: %s" % self.lockfile.path)

        def ___release_lockfile(self):
            self.logger.debug("Releasing lock: %s" % self.lockfile.path)
            self.lockfile.release()

        ### release the hook when we're done
        self.add_exit_hook( ___release_lockfile, self )

    def add_cli_arguments(self, parser):
        """
        Any additional CLI arguments that (super) classes might want
        to add. This method is overridable.
        """
        pass

    def add_exit_hook(self, hook, *args, **kwargs):
        """
        Adds the given function as an exit hook. The function will be called
        with the given positional and keyword arguments when the
        application's exit() method is called.
        """
        hook = partial(hook, *args, **kwargs)
        self._exit_hooks.append(hook)

    def _run_exit_hooks(self):
        """
        Run any exit hooks that are defined. Called from
        exit() and raise_critical_error()
        """

        for hook in self._exit_hooks:
            try:
                self.logger.debug("Running exit hook %s" % hook)
                hook()
            except Exception:
                self.logger.exception(
                    'krux.cli.Application.exit: Exception raised by exit hook.'
                )


    def exit(self, code=0):
        """
        Shut down the application and exit with the given status code.

        Calls all of the defined exit hooks before exiting. Exceptions are
        caught and logged.
        """

        self.logger.debug('Explicitly exiting application with code %d' % code)
        self._run_exit_hooks()
        exit(code)

    def raise_critical_error(self, err):
        """
        This logs the error, releases any lock files and throws an exception.
        The expectation is that the application exits after this.
        """

        self.logger.critical(err)
        self._run_exit_hooks()
        raise CriticalApplicationError(err)


##########################
### Functional interface #
##########################
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


def add_logging_args(parser):
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
        choices=LEVELS.keys(),
        help='Verbosity of logging. (default: %(default)s)'
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


def get_parser(description="Krux CLI", logging=True, stats=True, **kwargs):
    """
    Run setup and return an argument parser for Krux applications

    :keyword string description: Branding for the usage output.
    :keyword bool logging: Enable standard logging arguments.
    :keyword bool stats: Enable standard stats argument.

    All other keywords are passed verbatim to
    :py:class:`argparse.ArgumentParser`
    """
    parser = ArgumentParser(description=description, **kwargs)

    ### standard logging arguments
    if logging:
        parser = add_logging_args(parser)

    ### standard stats arguments
    if stats:
        parser = add_stats_args(parser)

    return parser
