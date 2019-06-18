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

from builtins import object
from mock import MagicMock, call

#
# Internal libraries
#

from krux.wrapper import Wrapper


class TestWrapper(Wrapper):
    z = 3

    def _get_wrapper_function(self, func):
        def wrap(*args, **kwargs):
            self._logger.info('Calling function %s', func.__name__)
            return func(*args, **kwargs)

        return wrap


class TestObject(object):
    x = 1

    def y(self, value):
        return {'Name': 'y', 'Value': value}


class WrapperTest(unittest.TestCase):

    def setUp(self):
        self._logger = MagicMock()
        self._stats = MagicMock()

        self._object = TestObject()

        self._wrapper = TestWrapper(
            wrapped=self._object,
            logger=self._logger,
            stats=self._stats,
        )

    def test_init(self):
        """
        krux.wrapper.Wrapper.__init__() correctly uses all passed variables
        """
        self.assertEqual(self._object, self._wrapper._wrapped)

    def test_wrapper_property(self):
        """
        krux.wrapper.Wrapper correctly returns the value of the wrapper's property
        """
        self.assertEqual(TestWrapper.z, self._wrapper.z)
        self.assertFalse(self._logger.debug.called)

    def test_wrapped_property(self):
        """
        krux.wrapper.Wrapper correctly falls back to the wrapped's property when it is not overriden by the wrapper
        """
        self.assertEqual(self._object.x, self._wrapper.x)

        debug_calls = [
            call("Attribute %s is not defined directly in this class. Looking up the wrapped object", 'x'),
            call("Found value %s for the attribute %s in the wrapped object", self._object.x, 'x'),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

    def test_wrapped_function(self):
        """
        krux.wrapper.Wrapper correctly calls the wrapped's function when it is not overriden by the wrapper
        """
        value = 2
        self.assertEqual(self._object.y(value), self._wrapper.y(value))

        debug_calls = [
            call(
                "Attribute %s is not defined directly in this class. Looking up the wrapped object",
                self._object.y.__name__,
            ),
            call("Found function %s in the wrapped object", self._object.y.__name__),
        ]
        self.assertEqual(debug_calls, self._logger.debug.call_args_list)

    def test_get_wrapper_function(self):
        """
        krux.wrapper.Wrapper._get_wrapper_function() correctly provides a way to wrap the wrapped's function
        """
        self._wrapper.y(2)

        self._logger.info.assert_called_once_with('Calling function %s', self._object.y.__name__)
