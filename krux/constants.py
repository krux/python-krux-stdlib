# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Constants for the Krux Python library
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import

######################
# Logging
######################
#:
DEFAULT_LOG_LEVEL = 'warning'

######################
# Stats
######################
#:
DEFAULT_STATSD_HOST = 'localhost'
#:
DEFAULT_STATSD_PORT = 8125
#:
DEFAULT_STATSD_ENV = 'dev'

######################
# CLI
######################
#:
DEFAULT_LOCK_DIR     = '/tmp'
DEFAULT_LOCK_TIMEOUT = 2    # in seconds
