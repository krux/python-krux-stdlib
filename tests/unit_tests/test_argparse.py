# -*- coding: utf-8 -*-
#
# © 2017 Krux Digital, A Salesforce Company
#
"""
Unit tests for the krux.argparse module.
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import
from argparse import ArgumentParser
from itertools import chain

#########################
# Third Party Libraries #
#########################
from nose.tools import assert_equal, assert_true

######################
# Internal Libraries #
######################
from krux.argparse import AppendOverDefault


DEFAULT = ['127.0.0.1']


def test_append_none_specified():
    """
    AppendOverDefault uses default when no options are specified.
    """
    parser = ArgumentParser()
    parser.add_argument('--ips', action=AppendOverDefault, default=DEFAULT)
    options = parser.parse_args([])

    assert_equal(options.ips, DEFAULT)


def test_append_one_specified():
    """
    AppendOverDefault overwrites the default when a single option is specified.
    """
    specified = '1.2.3.4'

    parser = ArgumentParser()
    parser.add_argument('--ips', action=AppendOverDefault, default=DEFAULT)
    options = parser.parse_args(['--ips', specified])

    assert_true(specified in options.ips)
    assert_true(DEFAULT not in options.ips)


def test_append_multiple_specified():
    """
    AppendOverDefault overwrites default when multiple options are specified.
    """
    specified = ['1.2.3.4', '5.6.7.8']
    args = chain.from_iterable([('--ips', s) for s in specified])

    parser = ArgumentParser()
    parser.add_argument('--ips', action=AppendOverDefault, default=DEFAULT)
    options = parser.parse_args(args)

    for s in specified:
        assert_true(s in options.ips)

    assert_true(DEFAULT not in options.ips)
