# -*- coding: utf-8 -*-
#
# © 2016-2017 Salesforce.com, inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
from abc import ABCMeta

#
# Third party libraries
#

#
# Internal libraries
#

from krux.logging import get_logger
from krux.stats import get_stats


class Object(object):
    """
    An abstract class to handle the common Krux coding pattern

    .. seealso::  https://docs.python.org/2/library/abc.html
    """

    __metaclass__ = ABCMeta

    def __init__(self, name=None, logger=None, stats=None):
        """
        Basic init method that sets up name, logger, and stats

        :param name: Name of the application
        :type name: str
        :param logger: Logger, recommended to be obtained using krux.cli.Application
        :type logger: logging.Logger
        :param stats: Stats, recommended to be obtained using krux.cli.Application
        :type stats: kruxstatsd.StatsClient
        """
        # Call to the superclass to bootstrap.
        super(Object, self).__init__()

        # Private variables, not to be used outside this module
        self._name = name if name is not None else self.__class__.__name__
        self._logger = logger if logger is not None else get_logger(self._name)
        self._stats = stats if stats is not None else get_stats(prefix=self._name)
