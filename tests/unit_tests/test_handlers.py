# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Tests for krux.tornado.handlers
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from logging    import Logger

import time
import unittest as unit

#########################
# Third Party Libraries #
#########################
from mock               import MagicMock, PropertyMock, patch
from nose.tools         import assert_equal, raises
from tornado.httpserver import HTTPRequest
from tornado.web        import HTTPError

######################
# Internal Libraries #
######################
from krux.tornado import Application
from krux.tornado import ErrorHandler, RequestHandler, StatusHandler


__author__ = 'Paul Lathrop'


class BaseCase(unit.TestCase):
    """
    Base class for krux.tornado.handlers tests.
    """
    def setUp(self):
        """
        Create mock application and request objects for the tests.
        """
        self.app = MagicMock(name = 'app', spec = Application)
        self.app.ui_methods = {}
        self.app.ui_modules = {}

        self.request = MagicMock(name = 'request', spec = HTTPRequest)


class TestRequestHandler(BaseCase):
    def setUp(self):
        """
        Create a mock logger object for the tests.
        """
        super(TestRequestHandler, self).setUp()

        self.logger     = MagicMock(name = 'logger', spec = Logger)
        self.app.logger = self.logger

    def test_prepare(self):
        """
        prepare() starts the timer for the request
        """
        start_time = time.time()
        handler    = RequestHandler(self.app, self.request)

        with patch(
                'krux.tornado.handlers.time.time',
                autospec     = True,
                return_value = start_time
        ) as mock_time:
            handler.prepare()

        mock_time.assert_called_once_with()
        assert_equal(handler.start_time, start_time)

    def test_get_stats_key_no_args(self):
        """
        get_stats_key() with no path arguments
        """
        self.request.path   = '/test'
        expected            = 'test'

        handler             = RequestHandler(self.app, self.request)
        handler.path_args   = []
        handler.path_kwargs = {}

        key = handler.get_stats_key()

        assert_equal(key, expected)

    # NOTE: We don't test with *both* path_args and path_kwargs because
    # tornado does not allow both to be set (but this logic occurs at a
    # completely different point in the flow than we are testing here).
    def test_get_stats_key_with_args(self):
        """
        get_stats_key() with path arguments
        """
        self.request.path   = '/test/banana/apple'
        expected            = 'test'

        handler             = RequestHandler(self.app, self.request)
        handler.path_args   = ['banana', 'apple']
        handler.path_kwargs = {}

        key = handler.get_stats_key()

        assert_equal(key, expected)

    # NOTE: We don't test with *both* path_args and path_kwargs because
    # tornado does not allow both to be set (but this logic occurs at a
    # completely different point in the flow than we are testing here).
    def test_get_stats_key_with_kwargs(self):
        """
        get_stats_key() with path keyword arguments
        """
        self.request.path   = '/test/banana/apple'
        expected            = 'test'

        handler             = RequestHandler(self.app, self.request)
        handler.path_args   = []
        handler.path_kwargs = {
            'monkey': 'banana',
            'donkey': 'apple',
        }

        key = handler.get_stats_key()

        assert_equal(key, expected)

    def test_get_stats_key_complex_path(self):
        """
        get_stats_key() with a multi-level path
        """
        self.request.path   = '/test/banana/apple'
        expected            = 'test.banana.apple'

        handler             = RequestHandler(self.app, self.request)
        handler.path_args   = []
        handler.path_kwargs = {}

        key = handler.get_stats_key()

        assert_equal(key, expected)

    def test_get_stats_key_http_error(self):
        """
        get_stats_key() with an HTTP error
        """
        self.request.path   = '/test/banana/apple'
        expected            = 'test'
        mock_status         = MagicMock(return_value = 404)

        handler             = RequestHandler(self.app, self.request)
        handler.path_args   = []
        handler.path_kwargs = {}
        handler.get_status  = mock_status

        key = handler.get_stats_key()

        mock_status.assert_called_once_with()
        assert_equal(key, expected)

    def test_send_stats(self):
        """
        send_stats() calls the correct stats methods
        """
        key      = 'test.banana'
        method   = 'get'
        end_time = time.time()
        delta    = .001
        status   = 200

        expected_incr  = '.'.join((key, method.upper(), str(status)))
        expected_timer = '.'.join((key, method.upper()))
        expected_delta = delta * 1000

        mock_get_key      = MagicMock(return_value = key)
        mock_get_status   = MagicMock(return_value = status)
        mock_incr         = MagicMock()
        mock_timer        = MagicMock()
        mock_stats        = MagicMock()
        mock_stats.incr   = mock_incr
        mock_stats.timing = mock_timer

        self.app.endpoint_stats = mock_stats
        self.request.method     = method

        handler               = RequestHandler(self.app, self.request)
        handler.get_stats_key = mock_get_key
        handler.start_time    = end_time - delta

        with patch(
                'krux.tornado.handlers.time.time',
                autospec     = True,
                return_value = end_time
        ) as mock_time:
            handler.send_stats()

        mock_get_key.assert_called_once_with()
        mock_incr.assert_called_once_with(expected_incr)
        mock_timer.assert_called_once_with(expected_timer, expected_delta)

    def test_on_finish(self):
        """
        on_finish() calls send_stats()
        """
        with patch(
                'krux.tornado.handlers.RequestHandler.send_stats',
                autospec = True,
        ) as mock_stats:
            handler = RequestHandler(self.app, self.request)
            handler.on_finish()

        mock_stats.assert_called_once_with(handler)


class TestErrorHandler(BaseCase):
    def test_initialize(self):
        """
        initialize() sets a 404 status
        """
        handler = ErrorHandler(self.app, self.request)
        assert_equal(handler._status_code, 404)

    @raises(HTTPError)
    def test_prepare(self):
        """
        prepare() raises an HTTPError
        """
        handler = ErrorHandler(self.app, self.request)
        handler.prepare()

    def test_get_stats_key(self):
        """
        get_stats_key() returns the correct catchall stats key
        """
        self.app.endpoint = 'test'
        expected          = 'test._catchall'

        handler = ErrorHandler(self.app, self.request)
        key     = handler.get_stats_key()

        assert_equal(key, expected)


class testStatusHandler(BaseCase):
    def test_status_dispatch(self):
        """
        status() dispatches to the application's status method
        """
        status = "Testin' like a boss."
        self.app.status = MagicMock(return_value = status)

        handler = StatusHandler(self.app, self.request)

        with patch(
                'krux.tornado.handlers.StatusHandler.send_status',
                autospec = True,
        ) as mock_send_status:
            handler.status()

        self.app.status.assert_called_once_with()
        mock_send_status.assert_called_once_with(handler, status)
