# -*- coding: utf-8 -*-
#
# © 2013, 2014 Krux Digital, Inc.
#

"""
Unit tests for the krux.cli module.
"""

#
# Standard Libraries
#
from __future__ import absolute_import
from unittest import TestCase

from logging import Logger
import multiprocessing
import os
import os.path
import time

#
# Third Party Libraries
#
from argparse import ArgumentParser, Namespace
from lockfile import LockError
from mock import MagicMock, patch
from nose.tools import *

import statsd

#
# Internal Libraries
#
import krux.cli as cli


def test_get_new_group():
    """
    Getting an argument group that doesn't exist.
    """
    name = 'new_group'
    mock_parser = MagicMock(spec=ArgumentParser)
    mock_parser._action_groups = []
    mock_parser.add_argument_group = MagicMock(return_value=name)

    group = cli.get_group(mock_parser, name)

    mock_parser.add_argument_group.assert_called_once_with(name)
    assert_equal(group, name)


def test_get_existing_group():
    """
    Getting an argument group that already exists.
    """
    name = 'existing'
    mock_group = MagicMock()
    mock_group.title = name
    mock_parser = MagicMock(spec=ArgumentParser)
    mock_parser._action_groups = [mock_group]

    group = cli.get_group(mock_parser, name)

    assert_equal(mock_parser.add_argument_group.call_count, 0)
    assert_equal(group, mock_group)


# XXX autospecing ArgumentParser does not autospec the private method
# we are (ab)using in krux.cli. So for now, just do the simplest test
# possible

# @patch('krux.cli.ArgumentParser', autospec=True)
def test_get_parser():
    """
    Test getting a parser from krux.cli
    """
    parser = cli.get_parser()
    assert_true(parser)


def test_get_script_name():
    """
    Test getting script name from the invoking script
    """
    name = cli.get_script_name()

    # these tests are invoked as 'nosetests --options...', so
    # that's the name of the 'script'
    assert_equal(name, 'nosetests')


class TestApplication(TestCase):
    def setUp(self):
        """
        Common test initialization
        """
        super(TestApplication, self).setUp()

        # Use all defaults for the CLI args.
        defaults = cli.get_parser().parse_args([])

        # Mock the command-line parser so it doesn't attempt to parse the
        # command line of our test runner.
        self.parser_patch = patch(
            'krux.cli.get_parser', spec=ArgumentParser
        )
        self.mock_parser = self.parser_patch.start()

        # Set up the mock parser to behave as if defaults were used.
        self.mock_parser.return_value.parse_args.return_value = defaults

        self.app = cli.Application(self.__class__.__name__)

    def tearDown(self):
        """
        Teardown steps for each Application test.
        """
        self.parser_patch.stop()

    def test_init(self):
        """
        krux.cli.Application initializion sets the expected attributes.
        """
        assert_equal(self.app.name, self.__class__.__name__)
        assert_true(isinstance(self.app.args, Namespace))
        assert_true(isinstance(self.app.logger, Logger))
        assert_true(isinstance(self.app.stats, statsd.StatsClient))
        assert_equal(self.app._exit_hooks, [])

    @patch('krux.cli.partial')
    def test_add_exit_hook(self, mock_partial):
        """
        krux.cli.Application.add_exit_hook adds a function to _exit_hooks.
        """
        mock_hook = MagicMock(return_value=True)

        self.app.add_exit_hook(mock_hook)

        mock_partial.assert_called_once_with(mock_hook)
        assert_equal(self.app._exit_hooks, [mock_partial.return_value])

    @patch('sys.exit')
    def test_exit_code(self, mock_exit):
        """
        krux.cli.Application.exit calls sys.exit with the provided exit code.
        """
        code = 255

        self.app.exit(code)

        mock_exit.assert_called_once_with(code)

    @patch('sys.exit')
    def test_exit_with_hook(self, mock_exit):
        """
        krux.cli.Application calls the exit hooks as expected.
        """
        mock_hooks = [MagicMock(return_value=True),
                      MagicMock(return_value=True)]

        for hook in mock_hooks:
            self.app.add_exit_hook(hook)
        self.app.exit(0)

        for hook in mock_hooks:
            hook.assert_called_once_with()

    @patch('sys.exit')
    def test_exit_with_hook_exception(self, mock_exit):
        """
        krux.cli.Application logs exceptions raised by
        """
        mock_hook = MagicMock(side_effect=ValueError)
        mock_logger = MagicMock(spec=Logger, autospec=True)

        app = cli.Application(self.__class__.__name__, logger=mock_logger)

        app.add_exit_hook(mock_hook)
        app.exit(0)

        assert_true(mock_logger.exception.called)


#
# Test krux.cli.Application
#

def test_application():
    """
    Test getting an Application from krux.cli
    """

    # Vanilla app
    with patch('sys.argv', [__name__]):
        app = cli.Application(name=__name__)
    assert_true(app)
    assert_true(app.parser)
    assert_true(app.stats)
    assert_true(app.logger)


def test_application_locks():
    """
    krux.cli.Application creates a lockfile which is reentrant
    """
    # just to make sure stale runs don't interfere
    name = __name__ + str(time.time())

    # Now with lockfile
    with patch('sys.argv', [__name__]):
        with patch('sys.exit'):
            app = cli.Application(name=name, lockfile=True)

            assert_true(app)
            assert_true(app.lockfile)

            # This will use the same lockfile, as it's based on pid.
            # so this should work
            app = cli.Application(name=name, lockfile=True)
            with app.context():
                assert_true(app)
                assert_true(app.lockfile)
                lock_file = app.lockfile.lock_file
                # make sure the lock file exists
                assert_true(os.path.exists(lock_file))
            # make sure the lock file has been removed
            assert_false(os.path.exists(lock_file))


def locker(name, event):
    app = cli.Application(name=name, lockfile=True)
    with app.context():
        event.set()
        while True:
            time.sleep(1)


@raises(LockError)
def test_application_lock_fail():
    """
    krux.cli.Application fails when it can't get a lock on the lockfile
    """
    event = multiprocessing.Event()
    name = __name__ + str(time.time())
    proc = multiprocessing.Process(name=name + ' locker',
                                   target=locker,
                                   args=(name, event))
    proc.start()
    # make sure the locker has initialized and locked its lockfile
    event.wait()
    with patch('sys.exit'):
        try:
            app = cli.Application(name=name, lockfile=True)
        finally:
            proc.terminate()
        # we should never get here but just in case...
        app.exit()
        assert_true(False)
