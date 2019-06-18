# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
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
from builtins import object
from functools import partial
from contextlib import contextmanager
import sys

import logging
import os.path
import __main__

#########################
# Third Party Libraries #
#########################
from lockfile import FileLock, LockError, UnlockError
from future.utils import raise_with_traceback

######################
# Internal Libraries #
######################
from krux.logging import DEFAULT_LOG_FACILITY
from krux.constants import DEFAULT_LOCK_TIMEOUT
import krux.io
import krux.stats
import krux.logging
from krux.parser import get_group, get_parser

####################
# Object interface #
####################


class ApplicationError(Exception):
    pass


class CriticalApplicationError(Exception):
    """
    This error is only raised if the application is expected to exit.
    It should never be caught.
    """
    pass


class Application(object):
    _VERSIONS = {}
    _WARNING_LOGGER_NAME = 'py.warnings'

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
        parser_args=None,
    ):
        """
        Wraps :py:class:`object` and sets up CLI argument parsing, stats and
        logging.

        :keyword string name: name of the application. Should be unique to Krux
        (required)

        :keyword parser: The CLI parser. Defaults to
        :py:func:`cli.get_parser <krux.cli.get_parser>`

        :keyword list parser_args: List of argument strings to be fed to parser, or else None.
        For testing purposes: Use to override the sys.argv command line arguments.
        """

        # note our name
        self.name = name

        # get a CLI parser
        #
        # Since this is a functional interface, we pass along whether or not stdout logging is desired
        # for a particular subclass/script
        #
        self.parser = parser or get_parser(description=name, logging_stdout_default=log_to_stdout)

        # get more arguments, if needed
        self.add_cli_arguments(self.parser)

        # and parse them
        self.args = self.parser.parse_args(args=parser_args)

        # the cli facility should over-ride the passed-in syslog facility
        syslog_facility = self.args.syslog_facility

        # same idea here, the cli value should over-ride the passed-in value
        if self.args.log_to_stdout != log_to_stdout:
            log_to_stdout = self.args.log_to_stdout
        self._init_logging(logger, syslog_facility, log_to_stdout)

        # get a stats object - any arguments are handled via the CLI
        # pass '--stats' to enable stats using defaults (see krux.cli)
        self.stats = krux.stats.get_stats(
            client=getattr(self.args, 'stats', None),
            prefix='cli.%s' % name,
            env=getattr(self.args, 'stats_environment', None),
            host=getattr(self.args, 'stats_host', None),
            port=getattr(self.args, 'stats_port', None),
        )

        # Set up an krux.io object so we can run external commands
        self.io = krux.io.IO(logger=self.logger, stats=self.stats)

        # Exit hooks are run when the exit() method is called.
        self._exit_hooks = []

        # Do you want an exclusive lock for this application?
        # This can be done later as well, with an explicit path
        self.lockfile = False

        if lockfile:
            self.acquire_lock(lockfile)

        # Many libraries uses warning module to send warnings to stderr. Let's capture them in our
        # logging so we can control them and save them.
        logging.captureWarnings(True)

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
        # Did you just tell us to use a lock, or did you give us a location?
        _lockfile = (os.path.join(self.args.lock_dir, self.name)
                     if lockfile is True
                     else lockfile)

        # this will throw an execption if anything goes wrong
        try:
            self.lockfile = FileLock(_lockfile)
            self.lockfile.acquire(timeout=DEFAULT_LOCK_TIMEOUT)
            self.logger.debug("Acquired lock: %s", self.lockfile.path)
        except LockError as err:
            self.logger.warning("Lockfile error occurred: %s", err)
            self.stats.incr("errors.lockfile_lock")
            raise
        except Exception:
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

        # release the hook when we're done
        self.add_exit_hook(___release_lockfile, self)

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
        raise_with_traceback(CriticalApplicationError(err))

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
        except Exception:
            # always run exit hooks, even on exceptions
            self._run_exit_hooks()
            raise
            # XXX: we may want to change this to log the exception and
            # automatically exit with a non-zero exit code

        # if the block finishes normally, call exit
        self.exit()


def get_script_name():
    # get the name of the script, without an extension
    name = os.path.splitext(os.path.basename(__main__.__file__))[0]
    # and replace underscores with dashes
    name = name.replace('_', '-')

    return name
