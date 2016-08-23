# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Miscellaneous utilities that don't have a better home.
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import

#########################
# Third Party Libraries #
#########################

######################
# Internal Libraries #
######################


def hasmethod(obj, method):
    """
    Return True if OBJ has an attribute named METHOD and that attribute is
    callable. Otherwise, return False.

    :argument object obj: an object
    :argument string method: the name of the method
    """
    return callable(getattr(obj, method, None))


def get_percentage(value, total, decimal_points=4, default=None):
    """
    @param value: value in int or double
    @param total: total in int or double
    @param decimal_points: how many decimal points for return result
    @param default: default return value if percentage cannot be calculated
    @return: the percentage: value of total.
    """
    return round(
        divide_or_zero(value * 1.0, total * 1.0, 0.0) * 100.0,
        decimal_points
    )


def divide_or_zero(numerator, denominator, default=None):
    """
    @param numerator: numerator
    @param denominator: denominator
    @param default: default return
    @return: numerator / denominator
    """
    if denominator == 0:
        return default
    return numerator / denominator


def flatten(lst):
    """
    Flattens a mixture of lists and objects into a one-dimensional list

    https://rosettacode.org/wiki/Flatten_a_list#Generative

    :param lst: :py:class:`list` List to flatten
    """
    for x in lst:
        if isinstance(x, list):
            for y in flatten(x):
                yield y
        else:
            yield x
