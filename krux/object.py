# © Copyright 2013-2020 Salesforce.com, inc.
from __future__ import generator_stop

from abc import ABCMeta

from krux.logging import get_logger
from krux.stats import get_stats


class Object(object, metaclass=ABCMeta):
    """
    An abstract class to handle the common Krux coding pattern

    .. seealso::  https://docs.python.org/2/library/abc.html
    """

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
