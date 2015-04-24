# -*- coding: utf-8 -*-
#
# © 2013-2015 Krux Digital, Inc.
#

"""
Instrument code for profiling and operational metrics.
"""

#
# Standard Libraries
#
from __future__ import absolute_import

import os
import socket

#
# Third Party Libraries
#
import statsd


ENV_VARS = ('KRUX_STATS_ENVIRONMENT',
            'STATS_ENVIRONMENT',
            'STATSD_ENVIRONMENT')
DEFAULT_STATS_ENVIRONMENT = 'dev'


def get_stats(prefix):
    """
    Return a correctly-configured StatsClient object using the standard
    Krux prefix prepended to the given PREFIX.

    The standard Krux prefix is $ENVIRONMENT.$HOSTNAME
    """
    prefix = '{0}.{1}'.format(get_standard_stats_prefix(), prefix)
    return statsd.StatsClient(prefix=prefix)


def get_standard_stats_prefix():
    """
    Return the krux standard stats prefix.
    """
    return '{0}.{1}'.format(get_stats_environment(), get_stats_hostname())


def get_stats_environment():
    """
    Return the correct stats environment based on environment variables.

    This function checks, in order, the environment variables
    KRUX_STATS_ENVIRONMENT, STATS_ENVIRONMENT, and STATSD_ENVIRONMENT,
    returning the first one that is defined.

    If none of these environment variables is defined, the function returns
    DEFAULT_STATS_ENVIRONMENT.
    """
    for env_key in ENV_VARS:
        env = os.getenv(env_key, None)
        if env is not None:
            return env

    return DEFAULT_STATS_ENVIRONMENT


def get_stats_hostname():
    """
    Return the hostname of the current host for use as part of the standard
    Krux stats prefix.
    """
    return socket.gethostname().split('.')[0]
