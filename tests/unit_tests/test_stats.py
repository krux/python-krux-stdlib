# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Unit tests for the krux.stats module.
"""
from __future__ import absolute_import
__author__ = 'Jos Boumans'

#########################
# Third Party Libraries #
#########################

from mock       import patch, call
from nose.tools import assert_true, assert_false
from pprint     import pprint

######################
# Internal Libraries #
######################
import krux.stats

from krux.stats import DummyStatsClient

def test_get_stats():
    """
    Test getting a stats object from krux.stats
    """
    stats = krux.stats.get_stats(prefix = 'real_app')

    ### object, and of the right class?
    assert_true(stats)
    assert_false(isinstance(stats, DummyStatsClient))

def test_get_dummy_stats():
    """
    Test getting a fakse stats object from krux.stats
    """
    stats = krux.stats.get_stats(prefix = 'dummy_app', client = False)

    ### object, and of the right class?
    assert_true(stats)
    assert_true(isinstance(stats, DummyStatsClient))


