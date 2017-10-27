# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
"""
This module provides a base class for tornado applications.

See :py:mod:`tornado.application <krux.tornado.application>` and
:py:mod:`tornado.handlers <krux.tornado.handlers>` for detailed
documentation.

Usage::

        from krux.tornado import Application


        if __name__ == '__main__':
            app = Application(name = 'my_app', endpoint = '/my_endpoint')
            app.start()
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import

######################
# Internal Libraries #
######################
from krux.tornado.application import Application
from krux.tornado.handlers import ErrorHandler, RequestHandler, StatusHandler
