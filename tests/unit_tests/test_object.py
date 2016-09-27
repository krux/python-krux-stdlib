# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest

#
# Third party libraries
#

from mock import MagicMock, patch

#
# Internal libraries
#

from krux.object import Object


class TestObject(Object):
    """
    Just needed a subclass of Object for unit test.
    Nothing to see here. Move along.
    """
    pass


class ObjectTest(unittest.TestCase):
    FAKE_NAME = 'fake-application'

    def test_init(self):
        """
        __init__() correctly uses all passed variables
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
        __init__() correctly generates default objects when no argument is passed
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
        app = TestObject()

        self.assertEqual(TestObject.__name__, app._name)
