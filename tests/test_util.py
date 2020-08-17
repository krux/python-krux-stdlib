# Copyright 2013-2020 Salesforce.com, inc.
"""
Tests for the krux.util module.
"""
from __future__ import generator_stop
import time
import unittest

import pytest
from nose.tools import assert_false, assert_true

from krux import util


class AnObject(object):
    a_class_property = None

    def __init__(self):
        self.an_instance_property = None

    def a_method(self):
        pass

    @classmethod
    def a_class_method(cls):
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
        assert_false(util.hasmethod(self.an_object, 'invalid'))

    def test_hasmethod_class_property(self):
        """
        hasmethod returns False for a non-callable class property.
        """
        assert_false(util.hasmethod(self.an_object, 'a_class_property'))

    def test_hasmethod_method(self):
        """
        hasmethod returns True for a callable instance method.
        """
        assert_true(util.hasmethod(self.an_object, 'a_method'))

    def test_hasmethod_class_method(self):
        """
        hasmethod returns True for a callable class method.
        """
        assert_true(util.hasmethod(self.an_object, 'a_class_method'))

    def test_hasmethod_property_method(self):
        """
        hasmethod returns False for an @property method.
        """
        assert_false(util.hasmethod(self.an_object, 'a_property_method'))


class FlattenTest(unittest.TestCase):
    def test_empty_list(self):
        """
        flatten yields an empty list when passed an empty list
        """
        self.assertEqual([], list(util.flatten([])))

    def test_flatten(self):
        """
        flatten yields a one-dimensional list when passed a multi-dimensional list of values
        """
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8], list(util.flatten([[1], 2, [[3, 4], 5], [[[]]], [[[6]]], 7, 8, []])))


delim = util._args_kwargs_delimiter
args_hash = util._function_args_hash
function_ags_hash_testdata = (
    (args_hash(),                             hash((      delim,                      ))),
    (args_hash(None, None),                   hash((      delim,                      ))),
    (args_hash([1], None),                    hash((1,    delim,                      ))),
    (args_hash([1, 2], None),                 hash((1, 2, delim,                      ))),
    (args_hash(None, {'a': 'b'}),             hash((      delim, ('a', 'b')           ))),
    (args_hash(None, {'a': 'b', 'c': 'd'}),   hash((      delim, ('a', 'b'), ('c', 'd')))),
    (args_hash([1], {'a': 'b'}),              hash((1,    delim, ('a', 'b')           ))),
    (args_hash([1, 2], {'a': 'b', 'c': 'd'}), hash((1, 2, delim, ('a', 'b'), ('c', 'd')))),
)


@pytest.mark.parametrize("test,expected", function_ags_hash_testdata)
def test_function_ags_hash(test, expected):
    assert test == expected


def test_cache_wrapper():
    wrapper = util.cache_wrapper(lambda _: _)
    assert wrapper(1) == 1
    assert wrapper(1) == 1
    assert wrapper(2) == 2


never_timeout_cache_call_count = 0


@util.cache
def never_timeout_cache(key):
    global never_timeout_cache_call_count
    never_timeout_cache_call_count = never_timeout_cache_call_count + 1
    return key * 2


def test_never_timeout_cache_called_once():
    never_timeout_cache(2)
    never_timeout_cache(2)
    assert never_timeout_cache_call_count == 1


def test_never_timeout_cache_valid_return_value():
    for _ in range(2):
        assert never_timeout_cache(2) == 4


always_timeout_cache_call_count = 0


@util.cache(expire_seconds=0)
def always_timeout_cache(key):
    global always_timeout_cache_call_count
    always_timeout_cache_call_count = always_timeout_cache_call_count + 1
    return key * 2


def test_always_timeout_cache_called_twice():
    always_timeout_cache(2)
    always_timeout_cache(2)
    assert always_timeout_cache_call_count == 2


def test_always_timeout_cache_valid_return_value():
    for _ in range(2):
        assert always_timeout_cache(2) == 4


timeout_cache_call_count = 0


@util.cache(expire_seconds=1)
def timeout_cache(key):
    global timeout_cache_call_count
    timeout_cache_call_count = timeout_cache_call_count + 1
    return key * 2


def test_timeout_cache_called_once():
    timeout_cache(2)
    timeout_cache(2)
    assert timeout_cache_call_count == 1


def test_timeout_cache_called_twice():
    time.sleep(2)
    timeout_cache(2)
    assert timeout_cache_call_count == 2


def test_timeout_cache_valid_return_value():
    for _ in range(2):
        assert timeout_cache(2) == 4
