# -*- coding: utf-8 -*-
#
# © 2017 Salesforce.com, inc.
#

#
# Standard libraries
#
from __future__ import absolute_import
import unittest

#
# Third party libraries
#
from mock import MagicMock, patch, call
from argparse import _ArgumentGroup, ArgumentParser

#
# Internal libraries
#
from krux.logging import LEVELS, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FACILITY
from krux.constants import (
    DEFAULT_STATSD_HOST,
    DEFAULT_STATSD_PORT,
    DEFAULT_STATSD_ENV,
    DEFAULT_LOCK_DIR,
)
from krux.parser import (
    get_parser,
    get_group,
    add_logging_args,
    add_stats_args,
    add_lockfile_args,
    KruxParser,
    KruxGroup,
)


class GetterTest(unittest.TestCase):
    FAKE_NAME = 'fake-application'
    FAKE_DESCRIPTION = 'fake-desc'

    @patch('krux.parser.add_logging_args')
    @patch('krux.parser.add_stats_args')
    @patch('krux.parser.add_lockfile_args')
    @patch('krux.parser.KruxParser')
    def test_get_parser_all(self, mock_parser_class, mock_lockfile, mock_stats, mock_logging):
        """
        krux.parser.get_parser() correctly create a KruxParser object based on the parameters
        """
        mock_parser_class.return_value = MagicMock()
        mock_logging.side_effect = lambda x, y: x
        mock_stats.side_effect = lambda x: x
        mock_lockfile.side_effect = lambda x: x

        parser = get_parser(True, True, True, True, self.FAKE_NAME, description=self.FAKE_DESCRIPTION)

        # Check whether the return value is correct
        self.assertEqual(mock_parser_class.return_value, parser)
        mock_parser_class.assert_called_once_with(self.FAKE_NAME, description=self.FAKE_DESCRIPTION)

        # Check whether the add_x_args functions were correctly called
        mock_logging.assert_called_once_with(parser, True)
        mock_stats.assert_called_once_with(parser)
        mock_lockfile.assert_called_once_with(parser)

    @patch('krux.parser.add_logging_args')
    @patch('krux.parser.add_stats_args')
    @patch('krux.parser.add_lockfile_args')
    @patch('krux.parser.KruxParser')
    def test_get_parser_none(self, mock_parser_class, mock_lockfile, mock_stats, mock_logging):
        """
        krux.parser.get_parser() correctly skips arguments when requested
        """
        mock_parser_class.return_value = MagicMock()

        parser = get_parser(logging=False, stats=False, lockfile=False)

        # Check whether the return value is correct
        self.assertEqual(mock_parser_class.return_value, parser)
        mock_parser_class.assert_called_once_with()

        # Check whether the ArgumentParser was created properly
        mock_parser_class.assert_called_once_with()

        # Check whether the add_x_args functions were correctly called
        self.assertFalse(mock_logging.called)
        self.assertFalse(mock_stats.called)
        self.assertFalse(mock_lockfile.called)

    @patch('krux.parser.add_logging_args')
    def test_get_parser_no_stdout(self, mock_logging):
        """
        krux.parser.get_parser() correctly sets the default value of the --log-to-stdout CLI argument
        """
        mock_logging.side_effect = lambda x, y: x

        parser = get_parser(logging_stdout_default=False)

        # Check whether the add_x_args functions were correctly called
        mock_logging.assert_called_once_with(parser, False)

    @patch('krux.parser.KruxParser')
    def test_get_group_new(self, mock_parser_class):
        """
        krux.parser.get_group() correctly creates a new _ArgumentGroup object when it does not exist
        """
        parser = mock_parser_class.return_value
        parser._action_groups = []
        env_var_prefix = False

        group = get_group(parser=parser, group_name=self.FAKE_NAME, env_var_prefix=env_var_prefix)

        # Check whether the return value is correct
        self.assertEqual(parser.add_argument_group.return_value, group)

        # Check whether the _ArgumentGroup was created correctly
        parser.add_argument_group.assert_called_once_with(
            title=self.FAKE_NAME, env_var_prefix=env_var_prefix
        )

    @patch('krux.parser.KruxParser')
    def test_get_group_existing(self, mock_parser_class):
        """
        krux.parser.get_group() correctly uses the existing _ArgumentGroup object
        """
        expected = MagicMock(title=self.FAKE_NAME)
        parser = mock_parser_class.return_value
        parser._action_groups = [expected, MagicMock(title='foo'), MagicMock(title='bar')]

        actual = get_group(parser=parser, group_name=self.FAKE_NAME)

        # Check whether the return value is correct
        self.assertEqual(expected, actual)

        # Check whether the caching worked properly
        self.assertFalse(parser.add_argument_group.called)


class AddTest(unittest.TestCase):
    def setUp(self):
        self._parser = MagicMock(spec=ArgumentParser, _action_groups=[])
        self._group = MagicMock(spec=_ArgumentGroup)
        self._parser.add_argument_group.return_value = self._group

    def test_add_logging_args_no_stdout(self):
        """
        krux.parser.add_logging_args() correctly sets up an _ArgumentGroup for log related arguments
        """
        actual = add_logging_args(parser=self._parser)

        # Check whether the return value is correct
        self.assertEqual(self._parser, actual)

        # Check whether an _ArgumentGroup was successfully created
        self._parser.add_argument_group.assert_called_once_with(title='logging', env_var_prefix=False)

        # Check whether the arguments were correctly created
        add_argument_calls = [
            call('--log-level', default=DEFAULT_LOG_LEVEL, choices=LEVELS.keys(), help='Verbosity of logging.'),
            call('--log-file', default=None, help='Full-qualified path to the log file'),
            call(
                '--no-syslog-facility',
                dest='syslog_facility',
                action='store_const',
                default=DEFAULT_LOG_FACILITY,
                const=None,
                env_var=False,
                add_default_help=False,
                help='disable syslog facility',
            ),
            call('--syslog-facility', default=DEFAULT_LOG_FACILITY, help='syslog facility to use'),
            call(
                '--no-log-to-stdout',
                dest='log_to_stdout',
                default=True,
                action='store_false',
                env_var=False,
                help='Suppress logging to stdout/stderr',
            ),
        ]
        self.assertEqual(add_argument_calls, self._group.add_argument.call_args_list)

    def test_add_logging_args_yes_stdout(self):
        """
        krux.parser.add_logging_args() correctly disables stdout logs by default when stdout_default is set to False
        """
        add_logging_args(parser=self._parser, stdout_default=False)

        # Check whether the arguments were correctly created
        add_argument_calls = [
            call('--log-level', default=DEFAULT_LOG_LEVEL, choices=LEVELS.keys(), help='Verbosity of logging.'),
            call('--log-file', default=None, help='Full-qualified path to the log file'),
            call(
                '--no-syslog-facility',
                dest='syslog_facility',
                action='store_const',
                default=DEFAULT_LOG_FACILITY,
                const=None,
                env_var=False,
                add_default_help=False,
                help='disable syslog facility',
            ),
            call('--syslog-facility', default=DEFAULT_LOG_FACILITY, help='syslog facility to use'),
            call(
                '--log-to-stdout',
                default=False,
                action='store_true',
                env_var=False,
                help='Log to stdout/stderr -- useful for debugging!',
            ),
        ]
        self.assertEqual(add_argument_calls, self._group.add_argument.call_args_list)

    def test_add_stats_args(self):
        """
        krux.parser.add_stats_args() correctly sets up an _ArgumentGroup for stats related arguments
        """
        actual = add_stats_args(parser=self._parser)

        # Check whether the return value is correct
        self.assertEqual(self._parser, actual)

        # Check whether an _ArgumentGroup was successfully created
        self._parser.add_argument_group.assert_called_once_with(title='stats', env_var_prefix=False)

        # Check whether the arguments were correctly created
        add_argument_calls = [
            call('--stats', default=False, action='store_true', help='Enable sending statistics to statsd.'),
            call('--stats-host', default=DEFAULT_STATSD_HOST, help='Statsd host to send statistics to.'),
            call('--stats-port', default=DEFAULT_STATSD_PORT, help='Statsd port to send statistics to.'),
            call('--stats-environment', default=DEFAULT_STATSD_ENV, help='Statsd environment.'),
        ]
        self.assertEqual(add_argument_calls, self._group.add_argument.call_args_list)

    def test_add_lockfile_args(self):
        """
        krux.parser.add_lockfile_args() correctly sets up an _ArgumentGroup for lock file related arguments
        """
        actual = add_lockfile_args(parser=self._parser)

        # Check whether the return value is correct
        self.assertEqual(self._parser, actual)

        # Check whether an _ArgumentGroup was successfully created
        self._parser.add_argument_group.assert_called_once_with(title='lockfile', env_var_prefix=False)

        # Check whether the arguments were correctly created
        add_argument_calls = [
            call('--lock-dir', default=DEFAULT_LOCK_DIR, help='Dir where lock files are stored'),
        ]
        self.assertEqual(add_argument_calls, self._group.add_argument.call_args_list)


class KruxParserTest(unittest.TestCase):
    def setUp(self):
        self._parser = KruxParser()

    @patch('krux.parser.KruxGroup')
    def test_add_argument_group(self, mock_group_class):
        """
        krux.parser.KruxParser.add_argument_group() correctly creates and returns a KruxGroup object
        """
        env_var_prefix = False
        title = 'fake-title'

        group = self._parser.add_argument_group(env_var_prefix=env_var_prefix, title=title)

        # Check whether the return value is correct
        self.assertEqual(mock_group_class.return_value, group)

        # Check whether the KruxGroup object was created correctly
        mock_group_class.assert_called_once_with(
            env_var_prefix=env_var_prefix,
            container=self._parser,
            title=title,
        )

        # Check whether the KruxGroup object was added to the list
        self.assertIn(mock_group_class.return_value, self._parser._action_groups)


class KruxGroupTest(unittest.TestCase):
    FAKE_TITLE = 'fake-app'
    POSITIONAL_ARGUMENT = 'foo'
    OPTIONAL_ARGUMENT = '--bar'
    OPTIONAL_ARGUMENT_SECONDARY = '-b'
    DEFAULT_VALUE = 'bar'
    ENVIRONMENT_KEY = (FAKE_TITLE + '_' + OPTIONAL_ARGUMENT.lstrip('-')).replace('-', '_').upper()
    ENVIRONMENT_VALUE = 'baz'
    HELP_TEXT = 'help'

    def setUp(self):
        self._parser = KruxParser()
        self._group = KruxGroup(title=self.FAKE_TITLE, container=self._parser)

    def test_init_no_prefix(self):
        """
        krux.parser.KruxGroup.__init__() correctly sets prefix for the environment variable support by default
        """
        self._group = KruxGroup(env_var_prefix=None, title=self.FAKE_TITLE, container=self._parser)

        # Check whether the _env_prefix is correct
        self.assertEqual(self.FAKE_TITLE + '_', self._group._env_prefix)

    def test_init_str_prefix(self):
        """
        krux.parser.KruxGroup.__init__() correctly handles the prefix override
        """
        env_var_prefix = 'test'
        self._group = KruxGroup(env_var_prefix=env_var_prefix, title=self.FAKE_TITLE, container=self._parser)

        # Check whether the _env_prefix is correct
        self.assertEqual(env_var_prefix + '_', self._group._env_prefix)

    def test_init_false_prefix(self):
        """
        krux.parser.KruxGroup.__init__() correctly omits the prefix
        """
        self._group = KruxGroup(env_var_prefix=False, title=self.FAKE_TITLE, container=self._parser)

        # Check whether the _env_prefix is correct
        self.assertEqual('', self._group._env_prefix)

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_optional(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly updates the default value and help text for optional arguments
        """
        self._group.add_argument(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=self.HELP_TEXT,
        )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.ENVIRONMENT_VALUE,
            help=' '.join([
                self.HELP_TEXT,
                KruxGroup.HELP_ENV_VAR.format(key=self.ENVIRONMENT_KEY),
                KruxGroup.HELP_DEFAULT.format(default=self.DEFAULT_VALUE),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True)
    def test_add_argument_empty_env_var(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly falls back to the supplied default value when environment variable is not there
        """
        self._group.add_argument(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=self.HELP_TEXT,
        )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=' '.join([
                self.HELP_TEXT,
                KruxGroup.HELP_ENV_VAR.format(key=self.ENVIRONMENT_KEY),
                KruxGroup.HELP_DEFAULT.format(default=self.DEFAULT_VALUE),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_false_env_var(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly omits environment variable support if disabled
        """
        self._group.add_argument(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=self.HELP_TEXT,
            env_var=False,
        )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=' '.join([
                self.HELP_TEXT,
                KruxGroup.HELP_DEFAULT.format(default=self.DEFAULT_VALUE),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    def test_add_argument_given_env_var(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly uses the provided environment variable key
        """
        env_key = 'SOME_KEY'
        env_value = 'some-value'
        with patch.dict('krux.parser.environ', clear=True, values={env_key: env_value}):
            self._group.add_argument(
                self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
                default=self.DEFAULT_VALUE,
                help=self.HELP_TEXT,
                env_var=env_key,
            )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=env_value,
            help=' '.join([
                self.HELP_TEXT,
                KruxGroup.HELP_ENV_VAR.format(key=env_key),
                KruxGroup.HELP_DEFAULT.format(default=self.DEFAULT_VALUE),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_no_env_var_help(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly omits environment variable help text if disabled
        """
        self._group.add_argument(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=self.HELP_TEXT,
            add_env_var_help=False,
        )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.ENVIRONMENT_VALUE,
            help=' '.join([
                self.HELP_TEXT,
                KruxGroup.HELP_DEFAULT.format(default=self.DEFAULT_VALUE),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_no_default_help(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly omits default help text if disabled
        """
        self._group.add_argument(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=self.HELP_TEXT,
            add_default_help=False,
        )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.ENVIRONMENT_VALUE,
            help=' '.join([
                self.HELP_TEXT,
                KruxGroup.HELP_ENV_VAR.format(key=self.ENVIRONMENT_KEY),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_existing_default_help(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly omits default help text if already existing
        """
        existing = ' (default: lol)'
        self._group.add_argument(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.DEFAULT_VALUE,
            help=self.HELP_TEXT + existing,
        )

        mock_add_argument.assert_called_once_with(
            self.OPTIONAL_ARGUMENT, self.OPTIONAL_ARGUMENT_SECONDARY,
            default=self.ENVIRONMENT_VALUE,
            help=' '.join([
                self.HELP_TEXT + existing,
                KruxGroup.HELP_ENV_VAR.format(key=self.ENVIRONMENT_KEY),
            ]),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    def test_add_argument_positional(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly does not affect positional arguments
        """
        self._group.add_argument(self.POSITIONAL_ARGUMENT, help=self.HELP_TEXT)

        mock_add_argument.assert_called_once_with(self.POSITIONAL_ARGUMENT, help=self.HELP_TEXT)

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_no_long_option(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly throws exception if there is no long option
        """
        with self.assertRaises(ValueError) as context:
            self._group.add_argument(
                self.OPTIONAL_ARGUMENT_SECONDARY,
                default=self.DEFAULT_VALUE,
                help=self.HELP_TEXT,
            )

        self.assertEqual(
            'You must either disable the environment variable fall back or provide a long name for the option',
            str(context.exception),
        )

    @patch('krux.parser._ArgumentGroup.add_argument')
    @patch.dict('krux.parser.environ', clear=True, values={ENVIRONMENT_KEY: ENVIRONMENT_VALUE})
    def test_add_argument_invalid_option(self, mock_add_argument):
        """
        krux.parser.KruxGroup.add_argument() correctly throws exception if the option is invalid
        """
        with self.assertRaises(ValueError) as context:
            self._group.add_argument(
                '--',
                default=self.DEFAULT_VALUE,
                help=self.HELP_TEXT,
            )

        self.assertEqual('You must provide a valid name for the option', str(context.exception))
