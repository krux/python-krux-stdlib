# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
"""
Unit tests for the krux.cli module.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from unittest import TestCase

from logging import Logger
from time    import time

import os
import sys
import copy

#########################
# Third Party Libraries #
#########################
from argparse   import ArgumentParser, Namespace
from mock       import MagicMock, patch
from nose.tools import assert_equal, assert_true

######################
# Internal Libraries #
######################
from krux.stats     import DummyStatsClient
from krux.constants import DEFAULT_LOCK_DIR
from krux.logging   import DEFAULT_LOG_LEVEL

import krux.cli as cli


def test_get_new_group():
    """
    Getting an argument group that doesn't exist.
    """
    name                           = 'new_group'
    mock_parser                    = MagicMock(spec=ArgumentParser)
    mock_parser._action_groups     = []
    mock_parser.add_argument_group = MagicMock(return_value = name)

    group = cli.get_group(mock_parser, name)

    mock_parser.add_argument_group.assert_called_once_with(name)
    assert_equal(group, name)


def test_get_existing_group():
    """
    Getting an argument group that already exists.
    """
    name                       = 'existing'
    mock_group                 = MagicMock()
    mock_group.title           = name
    mock_parser                = MagicMock(spec=ArgumentParser)
    mock_parser._action_groups = [mock_group]

    group = cli.get_group(mock_parser, name)

    assert_equal(mock_parser.add_argument_group.call_count, 0)
    assert_equal(group, mock_group)


### XXX autospecing ArgumentParser does not autospec the private method
### we are (ab)using in krux.cli. So for now, just do the simplest test
### possible

#@patch('krux.cli.ArgumentParser', autospec=True)
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

    ### these tests are invoked as 'nosetests --options...', so
    ### that's the name of the 'script'
    assert_equal(name, 'nosetests')

class TestApplication(TestCase):

    def _get_parser(self, args=[]):
        """
        Returns a mock parser with the given arguments set

        :param args: :py:class:`list` List of str CLI arguments (i.e. ['--log-level', 'debug', '--log-file', 'foo.log'])
        """

        # Get the argparse namespace object with the given args
        parser = cli.get_parser()
        namespace = parser.parse_args(args)

        # Return a mock ArgumentParser object as a parser
        # It has a function called 'parse_args' with the return value is the namespace variable defined above
        return MagicMock(
            spec=ArgumentParser,
            parse_args=MagicMock(return_value=namespace)
        )

    def setUp(self):
        """
        Common test initialization
        """
        super(TestApplication, self).setUp()

        self.app = cli.Application(
            name=self.__class__.__name__,
            parser=self._get_parser()
        )

    def test_init(self):
        """
        krux.cli.Application initializion sets the expected attributes.
        """
        assert_equal(self.app.name, self.__class__.__name__)
        assert_true(isinstance(self.app.args, Namespace))
        assert_true(isinstance(self.app.logger, Logger))
        assert_true(isinstance(self.app.stats, DummyStatsClient))
        assert_equal(self.app._exit_hooks, [])

    @patch('krux.cli.get_group')
    def test_add_cli_arguments_without_version(self, mock_get_group):
        """
        krux.cli.Application correctly does not create --version arguments when version is not set
        """
        self.app._VERSIONS = {}

        self.app.add_cli_arguments(None)

        self.assertFalse(mock_get_group.called)

    @patch('krux.cli.get_group')
    def test_add_cli_arguments_with_version(self, mock_get_group):
        """
        krux.cli.Application correctly create --version arguments when version is set
        """
        self.app.name = 'Test Application'
        version = '1.2.3'
        self.app._VERSIONS = {
            self.app.name: version,
        }

        self.app.add_cli_arguments(None)

        mock_get_group.assert_called_once_with(self.app.parser, 'version')
        mock_get_group.return_value.add_argument.assert_called_once_with(
            '--version',
            action='version',
            version=' '.join([self.app.name, version]),
        )


    @patch('krux.cli.krux.logging.get_logger')
    def test_syslog_facility(self, mock_logger):
        app = cli.Application(
            name=self.__class__.__name__,
            parser=self._get_parser(args=['--syslog-facility', 'test-syslog'])
        )

        mock_logger.assert_called_once_with(
            self.__class__.__name__,
            level=DEFAULT_LOG_LEVEL,
            syslog_facility='test-syslog',
            log_to_stdout=True,
        )

    @patch('krux.cli.krux.logging.get_logger')
    def test_no_syslog_facility(self, mock_logger):
        app = cli.Application(
            name=self.__class__.__name__,
            parser=self._get_parser(args=['--no-syslog-facility'])
        )

        mock_logger.assert_called_once_with(
            self.__class__.__name__,
            level=DEFAULT_LOG_LEVEL,
            syslog_facility=None,
            log_to_stdout=True,
        )

    @patch('krux.cli.partial')
    def test_add_exit_hook(self, mock_partial):
        """
        krux.cli.Application.add_exit_hook adds a function to _exit_hooks.
        """
        mock_hook = MagicMock(return_value=True)

        self.app.add_exit_hook(mock_hook)

        mock_partial.assert_called_once_with(mock_hook)
        assert_equal(self.app._exit_hooks, [mock_partial.return_value])

    @patch('krux.cli.sys.exit')
    def test_exit_code(self, mock_exit):
        """
        krux.cli.Application.exit calls sys.exit with the provided exit code.
        """
        code = 255

        self.app.exit(code)

        mock_exit.assert_called_once_with(code)

    @patch('krux.cli.sys.exit')
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

    @patch('krux.cli.sys.exit')
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

    def test_raise_critical_error(self):
        """
        krux.cli.Application executes the exit hooks, logs, and wraps the error as CriticalApplicationError upon raise_critical_error call
        """
        # Mock a logger
        mock_logger = MagicMock(spec=Logger, autospec=True)
        app = cli.Application(self.__class__.__name__, logger=mock_logger)

        # Add an exit hook
        mock_hook = MagicMock(return_value=True)
        app.add_exit_hook(mock_hook)

        with self.assertRaises(cli.CriticalApplicationError):
            try:
                raise StandardError('Test Error')
            except Exception, e:
                app.raise_critical_error(e)

        mock_hook.assert_called_once_with()
        mock_logger.critical.assert_called_once_with(e)

    @patch('krux.cli.sys.exit')
    def test_context_success(self, mock_exit):
        """
        krux.cli.Application exits with 0 upon success
        """
        with self.app.context():
            # Executes somethings
            self.app.logger.info('Hello World')

        mock_exit.assert_called_once_with(0)

    def test_context_failure(self):
        """
        krux.cli.Application executes the exit hooks and re-raise the error upon failure
        """
        # Add an exit hook
        mock_hook = MagicMock(return_value=True)
        self.app.add_exit_hook(mock_hook)

        with self.assertRaises(StandardError):
            with self.app.context():
                raise StandardError('Test Error')

        mock_hook.assert_called_once_with()

    @patch('krux.cli.logging')
    def test_capturewarning(self, mock_logging):
        """
        krux.cli.Application captures all warnings and put them in the logs
        """
        app = cli.Application(
            name=self.__class__.__name__,
            parser=self._get_parser()
        )

        mock_logging.captureWarnings.assert_called_once_with(True)

    def test_args(self):
        """
        krux.cli.Application gets args that match sys.argv (minus the name of the executable)
        """
        command_line_args = sys.argv[1:]
        app = cli.Application(name=self.__class__.__name__)
        _namespace, args = app.parser.parse_known_args()
        self.assertEqual(args, command_line_args)


class OverrideArgsApplication(cli.Application):
    """
    Used by TestOverrideArgsApplication.
    """
    def __init__(self, *args, **kwargs):
        super(OverrideArgsApplication, self).__init__(*args, **kwargs)

    def add_cli_arguments(self, parser):
        super(OverrideArgsApplication, self).add_cli_arguments(parser)
        group = cli.get_group(parser, 'test_group')
        group.add_argument('--test-arg')


class TestOverrideArgsApplication(TestCase):
    def test_override_args(self):
        """
        krux.cli.Application gets the args we hand it, in lieu of the os.environ args
        """
        test_arg = '--test-arg'
        test_value = 'test_value'
        test_args = [test_arg, test_value]
        test_attr = 'test_arg'
        app = OverrideArgsApplication(name=self.__class__.__name__,
                                      parser_args=test_args)
        self.assertEqual(getattr(app.args, test_attr), test_value)


###
### Test krux.cli.Application
###

def test_application():
    """
    Test getting an Application from krux.cli
    """

    ### Vanilla app
    with patch('sys.argv', [__name__]):
        app = cli.Application(name = __name__)
    assert_true(app)
    assert_true(app.parser)
    assert_true(app.stats)
    assert_true(app.logger)

def test_application_locks():
    ### just to make sure stale runs don't interfere
    name = __name__ + str(time())

    ### Now with lockfile
    with patch('sys.argv', [__name__]):
        app = cli.Application(name = name, lockfile = True)

        assert_true(app)
        assert_true(app.lockfile)

        ### This will use the same lockfile, as it's based on pid.
        ### so this should work
        app = cli.Application(name = name, lockfile = True)
        assert_true(app)
        assert_true(app.lockfile)

        ### needed to clean up lock file, or /tmp will get littered.
        app._run_exit_hooks()

        ### XXX ideally we'd have a failure test in here as well, but
        ### because of the way it's implemented LockFile won't fail if the
        ### same pid tries to get the same lock twice:
        ### http://pydoc.net/Python/lockfile/0.9.1/lockfile.linklockfile/
        ### suggestions welcome!
