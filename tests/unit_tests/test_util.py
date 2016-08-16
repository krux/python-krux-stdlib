# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Tests for the krux.util module.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import

import unittest

#########################
# Third Party Libraries #
#########################
from nose.tools import assert_false, assert_true

######################
# Internal Libraries #
######################
from krux.util import hasmethod


class AnObject(object):
    a_class_property = None

    def __init__(self):
        self.an_instance_propery = None

    def a_method(self):
        pass

    @classmethod
    def a_class_method(self):
        pass

    @property
    def a_property_method(self):
        pass


class TestUtil(unittest.TestCase):
    def setUp(self):
        """
        Setup for krux.util tests.
        """
        self.an_object = AnObject()

    def test_hasmethod_invalid_attr(self):
        """
        hasmethod returns False for an invalid attribute.
        """
        assert_false(hasmethod(self.an_object, 'invalid'))

    def test_hasmethod_class_property(self):
        """
        hasmethod returns False for a non-callable class property.
        """
        assert_false(hasmethod(self.an_object, 'a_class_property'))

    def test_hasmethod_method(self):
        """
        hasmethod returns True for a callable instance method.
        """
        assert_true(hasmethod(self.an_object, 'a_method'))

    def test_hasmethod_class_method(self):
        """
        hasmethod returns True for a callable class method.
        """
        assert_true(hasmethod(self.an_object, 'a_class_method'))

    def test_hasmethod_property_method(self):
        """
        hasmethod returns False for an @property method.
        """
        assert_false(hasmethod(self.an_object, 'a_property_method'))
