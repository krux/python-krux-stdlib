# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Unit tests for the krux.logging module.
"""
from __future__ import absolute_import
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

def test_get_logger():
    """
    Test getting a logger from krux.logging
    """
    logger = krux.logging.get_logger(__name__)
    assert_true(logger)




