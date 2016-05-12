# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Unit tests for the krux.logging module.
"""
from __future__ import absolute_import
import logging
__author__ = 'Jos Boumans'

#########################
# Third Party Libraries #
#########################

from mock       import patch, call
from nose.tools import assert_true
from pprint     import pprint

######################
# Internal Libraries #
######################

import krux.logging


TEST_LOGGER_NAME = 'test-logger'


def test_get_logger_basic():
    """
    Test getting a logger with no setup from krux.logging
    """
    with patch('krux.logging.setup') as mock_setup:
        with patch('krux.logging.syslog_setup') as mock_syslog_setup:
            krux.logging.get_logger(TEST_LOGGER_NAME, syslog_facility=None, log_to_stdout=False)

    assert_true(not mock_setup.called)
    assert_true(not mock_syslog_setup.called)
    assert_true(not logging.getLogger(TEST_LOGGER_NAME).propagate)


def test_get_logger_all():
    """
    Test getting a logger with all features enabled from krux.logging
    """
    with patch('krux.logging.setup') as mock_setup:
        with patch('krux.logging.syslog_setup') as mock_syslog_setup:
            krux.logging.get_logger(TEST_LOGGER_NAME, syslog_facility=krux.logging.DEFAULT_LOG_FACILITY, log_to_stdout=True, foo='bar')

    mock_setup.assert_called_once_with(foo='bar')
    mock_syslog_setup.assert_called_once_with(TEST_LOGGER_NAME, krux.logging.DEFAULT_LOG_FACILITY, foo='bar')
