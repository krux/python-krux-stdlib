# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
This module provides support for configuring the python logging module for
a Krux application.

Configuration is performed as part of the :py:func:`get_logger` call. This
call should happen early in your application's initialization (to prevent any
other libraries from initializing the root logger first.)

Usage::

        from krux.logging import get_logger

        if __name__ == '__main__':

            logger = get_logger(__name__, level='info')

The default log level for Krux applications in production is
:py:data:`krux.constants.DEFAULT_LOG_LEVEL`.

It is very important to use the correct log level for all your log
messages. Too much logging can have a significant impact on application
performance; too little logging makes it difficult to track down
problems. Here is a guide to what each log level means at Krux:

``debug``
    ``debug`` messages should be used to provide deep insight into exactly
    what actions your application is taking. You can be as verbose as you
    like with ``debug`` messages; they are intended to only be used when
    troubleshooting or in development. That said, there can be a
    performance impact if you are not careful: read
    http://docs.python.org/2.6/library/logging.html#optimization for more
    details. Do NOT use ``debug`` level messages for conditions which
    indicate the application is not functioning correctly.

``info``
    ``info`` messages should be used for higher-level messages about the
    application's functionality. Don't log ``info`` level messages for
    every step of an algorithm, but do use them to give an overview of what
    steps the application is taking. For example, an ``info`` message is
    appropriate when a connection to the database has been established
    successfully. Another use of ``info`` level messages is to output
    application settings at startup.

``warning``
    ``warning`` messages should indicate that a problem occurred but that
    the application was able to complete the operation succesfully. A good
    example would be attempting a Redis read which fails, but the read
    succeeds from another host. Intervention by a human should not be
    *necessary* to deal with ``warning`` level messages, but you *can* use
    them to signal a condition that it might be a good idea for a human to
    look at. You should be sparing with warning messages as it is common to
    run applications at log level ``warning`` in production. Do not use
    ``warning`` messages to indicate a complete failure to complete an
    operation. Also, do not use ``warning`` messages to to log normal
    events; avoid flooding the disk and sufferring performance penalties in
    production.

``error``
    ``error`` messages should indicate a problem occurred and the
    application was unable to complete the operation successfully, but
    there's no way to know, or no reason to expect, that all future
    operations will also fail. For example, an attempt to write to a Redis
    master failed. These messages usually indicate the some intervention is
    required, perhaps because data loss has occurred or a host is down,
    etc. ``error`` messages should be accompanied by putting the
    application in an error state; e.g. making ``__status`` fail for a web
    service, until requests stop failing. Be even more sparing with
    ``error`` level messages than you are with ``warning`` messages.

``critical``
    ``critical`` messages should indicate that a completely unrecoverable
    problem occurred and the application is unable to
    function. ``critical`` messages also indicate that the application has
    determined that all future requests will also fail. An application
    should ensure that all status checks fail when ``critical`` events
    occur. It may even be appropriate for the application to shut down or
    stop accepting traffic. These messages should be extremely rare in any
    application.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import

import logging

#############
# Constants #
#############
#: Map human-friendly log level strings to the constants in the
#: :py:mod:`python:logging` module.
LEVELS = dict((name, getattr(logging, name.upper()))
              for name in ('critical', 'error', 'warning', 'info', 'debug'))

#: The common `logging format
#: <http://docs.python.org/2.6/library/logging.html#formatter>`_ used by Krux
#: python applications.
FORMAT = '%(asctime)s: %(name)s/%(levelname)-9s: %(message)s'


#############
# Functions #
#############
def setup(level='warning'):
    """
    Configure the root logger for a Krux application.

    :keyword string level: log level, one of :py:data:`krux.logging.LEVELS`
    """
    assert level in LEVELS.keys(), 'Invalid log level %s' % level
    logging.basicConfig(format=FORMAT, level=LEVELS[level])


def get_logger(name, **kwargs):
    """
    Run setup and return the root logger for a Krux application.

    :argument name: the logging namespace to use, should usually be __name__

    All other keywords are passed verbatim to :py:func:`setup`
    """

    setup(**kwargs)
    return logging.getLogger(name)
