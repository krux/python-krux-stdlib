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
