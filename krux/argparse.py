# -*- coding: utf-8 -*-
#
# © 2017 Krux Digital, A Salesforce Company
#
"""
This module provides utilities/extensions for the
:py:mod:`python3:argparse` module.
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import
from argparse import Action


class AppendOverDefault(Action):
    """
    Argparse Action class which behaves similar to `action='append'`,
    but over-writes the default if and only if options are specified
    in the arguments. Example:

    >>> parser = ArgumentParser()
    >>> parser.add_argument('--ips', action=AppendOverDefault, default=['127.0.0.1'])
    >>> options = parser.parse_args([])
    >>> print options.ips
    ['127.0.0.1']

    >>> options = parser.parse_args(['--ips', '1.2.3.4'])
    >>> print options.ips
    ['1.2.3.4']

    >>> options = parser.parse_args(['--ips', '1.2.3.4', '--ips', '5.6.7.8'])
    >>> print options.ips
    ['1.2.3.4', '5.6.7.8']

    Note that just like `action='append'` this Action does not
    de-duplicate options:

    >>> options = parser.parse_args(['--ips', '1.2.3.4', '--ips', '1.2.3.4'])
    >>> print options.ips
    ['1.2.3.4', '1.2.3.4']
    """
    def __call__(self, parser, namespace, values, option_string=None):
        # This will be called once per incidence of the argument being
        # specified on the command line (and zero times if the option
        # is NOT specified). So, for the examples in the class
        # docstring, this code will be called zero, one, and two
        # times, respectively.
        if getattr(namespace, self.dest) == self.default:
            setattr(namespace, self.dest, [values])
        else:
            getattr(namespace, self.dest).append(values)
