# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

"""
Unit tests for the krux.stats module.
"""

#
# Standard Libraries
#
from __future__ import absolute_import

import unittest

#
# Third Party Libraries
#
from nose.tools import *
from mock import patch

import statsd

#
# Internal Libraries
#
import krux.stats


class TestStats(unittest.TestCase):
    def test_get_stats_return_type(self):
        """
        get_stats returns an instance of StatsClient.
        """
        stats = krux.stats.get_stats('')
        assert_true(isinstance(stats, statsd.StatsClient))

    def test_get_stats_prefix(self):
        """
        get_stats returns a correctly-prefixed StatsClient.
        """
        prefix = 'TestStats.test_get_stats_prefix'
        expected = '{0}.{1}'.format(
            krux.stats.get_standard_stats_prefix(),
            prefix
        )

        stats = krux.stats.get_stats(prefix)

        assert_equal(stats._prefix, expected)

    def test_get_stats_environment_default(self):
        """
        get_stats_environment returns the default when no env vars are set
        """
        with patch.dict('os.environ', {}):
            env = krux.stats.get_stats_environment()

        assert_equal(env, krux.stats.DEFAULT_STATS_ENVIRONMENT)

    def test_get_stats_environment_lookup(self):
        """
        get_stats_environment returns the correct value from env vars
        """
        for idx, env_key in enumerate(krux.stats.ENV_VARS):
            expected = 'env{0}'.format(idx)
            mock_env = {env_key: expected}

            with patch.dict('os.environ', mock_env):
                env = krux.stats.get_stats_environment()
                assert_equal(env, expected)

    def test_get_stats_environment_overlap(self):
        """
        get_stats_environment returns the value of the first env var
        """
        envs = ('prod', 'stage', 'dev')
        expected = envs[0]
        mock_env = dict(zip(krux.stats.ENV_VARS, envs))

        with patch.dict('os.environ', mock_env):
            env = krux.stats.get_stats_environment()

        assert_equal(env, expected)

    def test_get_stats_hostname(self):
        """
        get_stats_hostname returns the local host name
        """
        mock_host = 'teststats'
        mock_domain = 'test'
        mock_fqdn = '{0}.{1}'.format(mock_host, mock_domain)
        expected = mock_host

        with patch('socket.gethostname', return_value=mock_fqdn):
            hostname = krux.stats.get_stats_hostname()
            assert_equal(hostname, expected)

        with patch('socket.gethostname', return_value=mock_host):
            hostname = krux.stats.get_stats_hostname()
            assert_equal(hostname, expected)
