# Copyright 2013-2020 Salesforce.com, inc.
from __future__ import generator_stop
import unittest

from mock import MagicMock, patch

from krux.object import Object


class DummyObject(Object):
    """
    Just needed a subclass of Object for unit test.
    Nothing to see here. Move along.
    """
    pass


class ObjectTest(unittest.TestCase):
    FAKE_NAME = 'fake-application'

    def test_init(self):
        """
        krux.object.Object.__init__() correctly uses all passed variables
        """
        logger = MagicMock()
        stats = MagicMock()

        app = Object(
            name=self.FAKE_NAME,
            logger=logger,
            stats=stats
        )

        self.assertEqual(self.FAKE_NAME, app._name)
        self.assertEqual(logger, app._logger)
        self.assertEqual(stats, app._stats)

    @patch('krux.object.get_logger')
    @patch('krux.object.get_stats')
    def test_init_no_args(self, mock_stats, mock_logger):
        """
        krux.object.Object.__init__() correctly generates default objects when no argument is passed
        """
        app = Object()

        self.assertEqual(Object.__name__, app._name)
        mock_logger.assert_called_once_with(Object.__name__)
        self.assertEqual(mock_logger.return_value, app._logger)
        mock_stats.assert_called_once_with(prefix=Object.__name__)
        self.assertEqual(mock_stats.return_value, app._stats)

    def test_inheritance(self):
        """
        The default value of _name property for a subclass is handled correctly
        """
        app = DummyObject()

        self.assertEqual(DummyObject.__name__, app._name)
