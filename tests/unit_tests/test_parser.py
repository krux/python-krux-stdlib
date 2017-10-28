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

#
# Internal libraries
#

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
    @patch('krux.parser.ArgumentParser')
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
        self.assertEqual(KruxParser(wrapped=mock_parser_class.return_value), parser)

        # Check whether the ArgumentParser was created properly
        mock_parser_class.assert_called_once_with(self.FAKE_NAME, description=self.FAKE_DESCRIPTION)

        # Check whether the add_x_args functions were correctly called
        mock_logging.assert_called_once_with(parser, True)
        mock_stats.assert_called_once_with(parser)
        mock_lockfile.assert_called_once_with(parser)

    @patch('krux.parser.add_logging_args')
    @patch('krux.parser.add_stats_args')
    @patch('krux.parser.add_lockfile_args')
    @patch('krux.parser.ArgumentParser')
    def test_get_parser_none(self, mock_parser_class, mock_lockfile, mock_stats, mock_logging):
        """
        krux.parser.get_parser() correctly skips arguments when requested
        """
        mock_parser_class.return_value = MagicMock()

        parser = get_parser(logging=False, stats=False, lockfile=False)

        # Check whether the return value is correct
        self.assertEqual(KruxParser(wrapped=mock_parser_class.return_value), parser)

        # Check whether the ArgumentParser was created properly
        mock_parser_class.assert_called_once_with()

        # Check whether the add_x_args functions were correctly called
        self.assertFalse(mock_logging.called)
        self.assertFalse(mock_stats.called)
        self.assertFalse(mock_lockfile.called)

    @patch('krux.parser.add_logging_args')
    @patch('krux.parser.add_stats_args')
    @patch('krux.parser.add_lockfile_args')
    @patch('krux.parser.ArgumentParser')
    def test_get_parser_no_stdout(self, mock_parser_class, mock_lockfile, mock_stats, mock_logging):
        """
        krux.parser.get_parser() correctly sets the default value of the --log-to-stdout CLI argument
        """
        mock_parser_class.return_value = MagicMock()
        mock_logging.side_effect = lambda x, y: x
        mock_stats.side_effect = lambda x: x
        mock_lockfile.side_effect = lambda x: x

        parser = get_parser(logging_stdout_default=False)

        # Check whether the add_x_args functions were correctly called
        mock_logging.assert_called_once_with(parser, False)
