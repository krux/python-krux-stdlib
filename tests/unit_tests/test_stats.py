# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
"""
Unit tests for the krux.stats module.
"""
from __future__ import absolute_import
__author__ = 'Jos Boumans'

#
# Third Party Libraries #
#
from nose.tools import assert_true, assert_false

#
# Internal Libraries #
#
import krux.stats
from krux.stats import DummyStatsClient
import kruxstatsd
import statsd


def test_get_stats():
    """
    Test getting a stats object from krux.stats
    """
    stats = krux.stats.get_stats(prefix='dummy_app')

    # object, and of the right class?
    assert_true(stats)
    assert_false(isinstance(stats, DummyStatsClient))


def test_get_dummy_stats():
    """
    Test getting a false stats object from krux.stats
    """
    stats = krux.stats.get_stats(prefix='dummy_app', client=False)

    # object, and of the right class?
    assert_true(stats)
    assert_true(isinstance(stats, DummyStatsClient))


def test_get_legacy_client():
    """
    Test that a 'legacy' stats client is returned when requested
    """

    stats = krux.stats.get_stats(prefix='dummy_app', legacy_names=True)
    assert_true(isinstance(stats, kruxstatsd.StatsClient))


def test_get_default_client():
    """
    Test that the default is to return a bare statsd.StatsClient
    """
    stats = krux.stats.get_stats(prefix='dummy_app')
    assert_true(isinstance(stats, statsd.StatsClient))
