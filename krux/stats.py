# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
"""
Instrument code for profiling and operational metrics.
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import
from contextlib import contextmanager

#########################
# Third Party Libraries #
#########################
import statsd       # for the dummy client to wrap the callables
import kruxstatsd   # the default handler

######################
# Internal Libraries #
######################
from krux.constants import (
    DEFAULT_STATSD_HOST,
    DEFAULT_STATSD_PORT,
    DEFAULT_STATSD_ENV,
)


def get_stats(
    prefix,
    client=True,
    env=DEFAULT_STATSD_ENV,
    host=DEFAULT_STATSD_HOST,
    port=DEFAULT_STATSD_PORT,
    legacy_names=False,
):
    """
    Pick the stats implementation the caller wants.

    :argument prefix: The string prepended to all stats sent to Statsd.

    :parameter client: The StatsClient class to use. Defaults to 'True' which
    signals the use of 'statsd.StatsClient'. 'False' or 'None' will
    signal the use of :py:class:`stats.DummyStatsClient <krux.stats.DummyStatsClient>`.

    :parameter env: The Statsd environment to report the stat in. Defaults to
    :py:data:`krux.constants.DEFAULT_STATSD_ENV`

    :parameter host: The Statsd host to connect to. Defaults to
    :py:data:`krux.constants.DEFAULT_STATSD_HOST`

    :parameter port: The Statsd port to connect to. Defaults to
    :py:data:`krux.constants.DEFAULT_STATSD_PORT`

    :parameter legacy_names: If set, use the legacy kruxstatsd wrapper, which prefixes stats with the environment name,
    and suffixes them with the host name.
    """

    stats_client = {
        # You want the default implementation
        True:   statsd.StatsClient,
        # You don't want stats, use dummy class
        False:  DummyStatsClient,
        None:   DummyStatsClient,
        # Default: you have an object that
        # implements the StatsClient interface
    }.get(client)

    stats_client_args = {
        'prefix': prefix,
        'host': host,
        'port': port,
    }
    if legacy_names:
        stats_client = kruxstatsd.StatsClient
        stats_client_args['env'] = env

    stats = stats_client(**stats_client_args)
    # You passed something we can't deal with
    assert hasattr(stats, 'incr') and hasattr(stats, 'timer'), \
        "Unsupported value for 'client': %s" % client

    return stats


class DummyStatsClient(object):
    """A dummy StatsClient compatible object that does nothing"""

    def __init__(self, **kwargs):
        # So we have the object ready for wrapping
        self._client = statsd.StatsClient()

    def __getattr__(self, attr):
        """Proxies calls to ``statsd.StatsClient`` methods. Silently pass'es.
        """
        attr = getattr(self._client, attr)

        if callable(attr):
            # We define @contextmanager, because some functions can be used in
            # a 'with' statement - specifically 'timer'.
            # see http://docs.python.org/2/library/contextlib.html for details.
            # 'yield' makes sure the decorated function is called
            @contextmanager
            def wrapper(*args, **kwargs):
                yield
            return wrapper
        return attr
