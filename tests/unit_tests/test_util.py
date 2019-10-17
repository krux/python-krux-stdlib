# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
"""
Tests for the krux.util module.
"""
#
# Standard Libraries #
#
from __future__ import absolute_import
import unittest

#
# Third Party Libraries #
#
from builtins import object
from nose.tools import assert_false, assert_true

#
# Internal Libraries #
#
from krux.util import hasmethod, flatten


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


class HasMethodTest(unittest.TestCase):
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


class FlattenTest(unittest.TestCase):
    def test_empty_list(self):
        """
        flatten yields an empty list when passed an empty list
        """
        self.assertEqual([], list(flatten([])))

    def test_flatten(self):
        """
        flatten yields a one-dimensional list when passed a multi-dimensional list of values
        """
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8], list(flatten([[1], 2, [[3, 4], 5], [[[]]], [[[6]]], 7, 8, []])))
