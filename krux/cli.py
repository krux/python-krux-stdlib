# -*- coding: utf-8 -*-
#
# © 2013-2014 Krux Digital, Inc.
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
from contextlib import contextmanager
import sys
### This is still here in case something else is using it via an import.
### This should be removed.
from sys import exit

import logging
import os.path
import __main__

#########################
# Third Party Libraries #
#########################
from argparse import ArgumentParser
from lockfile import FileLock, LockError, UnlockError

######################
# Internal Libraries #
######################
from krux.logging import LEVELS, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FACILITY
from krux.constants import (
    DEFAULT_STATSD_HOST,
    DEFAULT_STATSD_PORT,
    DEFAULT_STATSD_ENV,
    DEFAULT_LOCK_DIR,
    DEFAULT_LOCK_TIMEOUT,
)
import krux.io
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
    _VERSIONS = {}

    """
    Krux base class for CLI applications

    :argument name: name of your CLI application
    """
    def __init__(
        self,
        name,
        parser=None,
        logger=None,
        lockfile=False,
        syslog_facility=DEFAULT_LOG_FACILITY,
        log_to_stdout=True,
    ):
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
        ###
        ### Since this is a functional interface, we pass along whether or not stdout logging is desired
        ### for a particular subclass/script
        ###
        self.parser = parser or krux.cli.get_parser(description=name, logging_stdout_default=log_to_stdout)

        ### get more arguments, if needed
        self.add_cli_arguments(self.parser)

        ### and parse them
        self.args = self.parser.parse_args()

        # the cli facility should over-ride the passed-in syslog facility
        syslog_facility = self.args.syslog_facility

        # same idea here, the cli value should over-ride the passed-in value
        if self.args.log_to_stdout != log_to_stdout:
            log_to_stdout = self.args.log_to_stdout
        self._init_logging(logger, syslog_facility, log_to_stdout)

        ### get a stats object - any arguments are handled via the CLI
        ### pass '--stats' to enable stats using defaults (see krux.cli)
        self.stats = krux.stats.get_stats(
            client=getattr(self.args, 'stats', None),
            prefix='cli.%s' % name,
            env=getattr(self.args, 'stats_environment', None),
            host=getattr(self.args, 'stats_host', None),
            port=getattr(self.args, 'stats_port', None),
        )

        ### Set up an krux.io object so we can run external commands
        self.io = krux.io.IO( logger = self.logger, stats = self.stats )

        ### Exit hooks are run when the exit() method is called.
        self._exit_hooks = []

        ### Do you want an exclusive lock for this application?
        ### This can be done later as well, with an explicit path
        self.lockfile = False

        if lockfile:
            self.acquire_lock(lockfile)

    def _init_logging(self, logger, syslog_facility, log_to_stdout):
        self.logger = logger or krux.logging.get_logger(
            self.name,
            level=self.args.log_level,
            syslog_facility=syslog_facility,
            log_to_stdout=log_to_stdout,
        )
        if self.args.log_file is not None:
            handler = logging.handlers.WatchedFileHandler(self.args.log_file)
            formatter = logging.Formatter(krux.logging.FORMAT)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def acquire_lock(self, lockfile=True):
        ### Did you just tell us to use a lock, or did you give us a location?
        _lockfile = (os.path.join(self.args.lock_dir, self.name)
                     if lockfile is True
                     else lockfile)

        ### this will throw an execption if anything goes wrong
        try:
            self.lockfile = FileLock(_lockfile)
            self.lockfile.acquire( timeout = DEFAULT_LOCK_TIMEOUT )
            self.logger.debug("Acquired lock: %s", self.lockfile.path)
        except LockError as err:
            self.logger.warning("Lockfile error occurred: %s", err)
            self.stats.incr("errors.lockfile_lock")
            raise
        except:
            self.logger.warning(
                "Unhandled exception while acquiring lockfile at %s", _lockfile
            )
            self.stats.incr("errors.lockfile_unhandled")
            raise

        def ___release_lockfile(self):
            self.logger.debug("Releasing lock: %s", self.lockfile.path)

            try:
                self.lockfile.release()
            except UnlockError as err:
                self.logger.warning("Lockfile error occurred unlocking: %s", err)
                self.stats.incr("errors.lockfile_unlock")
                raise

        ### release the hook when we're done
        self.add_exit_hook( ___release_lockfile, self )

    def add_cli_arguments(self, parser):
        """
        Any additional CLI arguments that (super) classes might want
        to add. This method is overridable.
        """
        version = self._VERSIONS.get(self.name)

        if version is not None:
            group = get_group(self.parser, 'version')

            group.add_argument(
                '--version',
                action='version',
                version=' '.join([self.name, version]),
            )

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
                self.logger.debug("Running exit hook %s", hook)
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

        self.logger.debug('Explicitly exiting application with code %d', code)
        self._run_exit_hooks()
        sys.exit(code)

    def raise_critical_error(self, err):
        """
        This logs the error, releases any lock files and throws an exception.
        The expectation is that the application exits after this.
        """

        self.logger.critical(err)
        self._run_exit_hooks()

        exc_info = sys.exc_info()
        if exc_info[1] is err:
            raise CriticalApplicationError, CriticalApplicationError(exc_info[1]), exc_info[2]
        else:
            raise CriticalApplicationError(err)

    @contextmanager
    def context(self):
        """
        Returns a context manager that you can use with the 'with' keyword.
        Using this context manager means that you do not need to explicitly
        call exit (if exiting with the default exit code of 0) and do no need
        to use raise_critical_error when raising exceptions as this context
        manager ensures that the exit hooks are always called (and hence the
        lockfile is always released).

        Ex:
        app = Application()
        with app.context():
            app.logger.info('Hello World')
            ...
        """
        try:
            yield
        except:
            # always run exit hooks, even on exceptions
            self._run_exit_hooks()
            raise
            # XXX: we may want to change this to log the exception and
            # automatically exit with a non-zero exit code

        # if the block finishes normally, call exit
        self.exit()


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
        choices=LEVELS.keys(),
        help='Verbosity of logging. (default: %(default)s)'
    )
    group.add_argument(
        '--log-file',
        default=None,
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
        help='syslog facility to use '
        '(default: %(default)s).'
    )
    ###
    ### If logging to stdout is enabled (the default, defined by the log_to_stdout arg
    ### in __init__(), we provide a --no-log-to-stdout cli arg to disable it.
    ###
    ### If our calling script or subclass chooses to disable stdout logging by default,
    ### we instead provide a --log-to-stdout arg to enable it, for debugging etc.
    ###
    ### This is particularly useful for Icinga monitoring scripts, where we don't want
    ### logging info to reach stdout during normal operation, because Icinga ingests
    ### everything that's written there.
    ###
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

def get_parser(description="Krux CLI", logging=True, stats=True, lockfile=True, logging_stdout_default=True, **kwargs):
    """
    Run setup and return an argument parser for Krux applications

    :keyword string description: Branding for the usage output.
    :keyword bool logging: Enable standard logging arguments.
    :keyword bool stats: Enable standard stats argument.
    :keyword bool logging_stdout_default: Whether or not logging to stdout is enabled (affects cli args setup)

    All other keywords are passed verbatim to
    :py:class:`argparse.ArgumentParser`
    """
    parser = ArgumentParser(description=description, **kwargs)

    ### standard logging arguments
    if logging:
        parser = add_logging_args(parser, logging_stdout_default)

    ### standard stats arguments
    if stats:
        parser = add_stats_args(parser)

    ### standard lockfile args
    if lockfile:
        parser = add_lockfile_args(parser)

    return parser


def get_script_name():
    # get the name of the script, without an extension
    name = os.path.splitext(os.path.basename(__main__.__file__))[0]
    # and replace underscores with dashes
    name = name.replace('_', '-')

    return name
