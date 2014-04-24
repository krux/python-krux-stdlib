# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
This module provides an Application base class for Krux tornado
applications. It provides standard command-line options for configuring a
tornado application the Krux Way.

Default handlers are provided for the status endpoint and any requests to
invalid URLs.

Subclasses can add handlers by setting the 'app_handlers' class or instance
attribute to a list of Tornado handler specifiers, or overriding
:py:meth:`add_app_handlers <Application.add_app_handlers>`.

Usage::

        from krux.tornado import Application


        class MyApplication(Application):
            # To add handlers at the class level:
            app_handlers = [(r'/handler', MyClassHandler)]

            def __init__(self, *args, **kwargs):
                # To add handlers at the instance level:
                self.app_handlers = [(r'/handler', MyInstanceHandler)]

            def status(self):
                # Over-ride the status() method to take advantage of
                # the default __status handler. Return something
                # JSON-encodable
                return {
                    'status': 'ok',
                    'message': 'chillin in da hood',
                }

            def add_arguments(self):
                # Over-ride the add_arguments method to add command-line
                # arguments for your application to the provided argument
                # parser.
                super(MyApplication, self).add_arguments()

                self.parser.add_argument('-f', '--file')


        if __name__ == '__main__':
            app = MyApplication(name='my_app', endpoint='/my_endpoint')
            app.start()
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import

import os
import os.path
import sys
import signal

######################
# Internal Libraries #
######################
from krux.tornado.handlers import ErrorHandler, StatusHandler

import krux.stats
import krux.logging
import krux.tornado.cli

#########################
# Third Party Libraries #
#########################
import git
import tornado.web
import tornado.ioloop


class Application(tornado.web.Application):
    """
    Krux base class for Tornado applications.
    """
    #: List of handler tuples in the format required by the constructor for
    #: :py:class:`tornado.web.Application`.
    app_handlers = []

    def __init__(
            self,
            name,
            endpoint,
            parser=None,
            cli_args=None,
            status_handler=StatusHandler,
            fallback_handler=ErrorHandler,
            *args,
            **kwargs
    ):
        """
        Wraps :py:class:`tornado.web.Application` and sets up CLI argument
        parsing, stats and status handlers.

        :argument string name: Name of the application. Should be unique among
                               Krux applications.

        :argument string endpoint: Endpoint the application listens on,
                                   like '/test'

        :argument list cli_args: List of arguments to use as command-line
                                 arguments instead of sys.argv (for tests)

        :keyword class status_handler: The request handler for '__status'.

        :keyword class fallback_handler: The request handler for unknown paths.

        :keyword object parser: The CLI parser. Defaults to the return value
                                of :py:func:`~krux.tornado.cli.get_parser`.

        All other keywords are passed verbatim to
        :py:class:`tornado.web.Application`
        """

        ### You /have/ to pass a prefix
        assert len(endpoint), 'You must pass an endpoint with length > 0'

        ### note our name
        self.name = name

        ### Set the application version.
        self.version = self.get_version()

        ### Configure a command-line parser and parse our command-line
        ### arguments.
        self.parser = parser or krux.tornado.cli.get_parser(description=name)
        self.add_arguments()
        self.args = self.parser.parse_args(cli_args)

        ### Tornado settings
        self.settings = {
            'debug': self.args.development,
            'gzip': True,
        }
        self.settings.update(kwargs)

        ### the endpoint for this application
        self.endpoint = endpoint.lstrip('/').rstrip('/')

        ### set up handlers
        ###
        ### We don't use add_handlers for this because it uses special logic
        ### that ends up not preserving the order of the handlers. Since we
        ### need the fallback handler to come last, it is critical that order
        ### be maintained.
        ###
        ### First, get any handlers that were passed in as settings.
        handlers = self.settings.get('handlers', [])

        ### Call the hook to allow subclasses to add their own handlers.
        handlers.extend(self.add_app_handlers())

        ### Finally add status and fallback handlers. As noted above, the
        ### fallback_handler *must* come last, so if you change this code,
        ### keep that in mind.
        handlers.extend([
            (r'/%s/__status/?' % self.endpoint, status_handler),
            (r'/.*/?$', fallback_handler)
        ])
        self.settings['handlers'] = handlers

        ### Initialize via tornado.web
        super(Application, self).__init__(*args, **self.settings)

        ### get a logger - is there a way to to have logger be relative to the
        ### invocation of the log call?
        self.logger = krux.logging.get_logger(name, level=self.args.log_level)

        ### Log settings at DEBUG
        self.logger.debug('Application settings: %s', self.settings)
        self.logger.debug('Application version: %s', self.version)

        ### get a stats object - any arguments are handled via the CLI
        ### pass '--stats' to enable stats using defaults (see krux.cli)
        self.stats = krux.stats.get_stats(
            client=self.args.stats,
            prefix='tornado.%s' % name,
            env=self.args.stats_environment,
            host=self.args.stats_host,
            port=self.args.stats_port,
        )

        ### we have another stats endpoint that's specifically for wrapping
        ### requests internally that uses a different prefix.
        self.endpoint_stats = krux.stats.get_stats(
            client=self.args.stats,
            prefix='tornado.%s.__url' % (name,),
            env=self.args.stats_environment,
            host=self.args.stats_host,
            port=self.args.stats_port,
        )

        ### debug info. handlers is a combo of regex & tornado.web.URLSpec
        ### objects:
        ### (<_sre.SRE_Pattern object at 0x107dcb0>,
        ### [<tornado.web.URLSpec object at 0x1285090>])
        self.logger.debug("*** Urls to handler mapping:")
        for handlers in self.handlers:

            ### the URLspec can be introspected:
            for spec in handlers[1]:
                klass = '.'.join((spec.handler_class.__module__,
                                  spec.handler_class.__name__))

                ### So, spec.reverse() only works if you don't use named
                ### params. To be safe, we'll just use the regex pattern
                ### and display that. It has the benefit of also showing
                ### the name of the capture params.
                self.logger.debug("***    %s -> %s" %
                                  (spec.regex.pattern, klass))

    def add_arguments(self):
        """
        Hook for subclasses to configure command-line arguments by adding them
        to ``self.parser``.
        """
        pass

    def add_app_handlers(self):
        """
        Hook for subclasses to configure additional handlers. Must return a
        list of tuples in the format required by the constructor for
        :py:class:`tornado.web.Application`. The default implementation
        returns :py:attr:`app_handlers`, if set, or an empty list.
        """
        return getattr(self, 'app_handlers', [])

    def get_version(self):
        """
        Return the version of the application. Called once, at application
        startup, to set the version of the running application.

        First, checks for a file named VERSION in the root of the
        distribution directory. If that file exists, a single line is read
        and returned as the version string.

        Next, checks if the distribution directory looks like a git
        repository. If it does, the HEAD commit is returned as the version
        string.

        Subclasses can over-ride this method in otder to use different
        logic to set the application version.
        """
        base_dir = os.getcwd()
        version_path = os.path.join(base_dir, 'VERSION')

        # TODO: It would be totally awesome if this would walk up the
        # directory tree to try to find .git in all the parent
        # directories. For now, it doesn't.
        git_path = os.path.join(base_dir, '.git')

        if os.path.exists(version_path):
            with open(version_path) as version_file:
                return version_file.readline().strip()

        if os.path.exists(git_path):
            return str(git.Repo(base_dir).commit())

        return None

    def start(
            self,
            http_port=None,
            address=None,
            blocking_log_threshold=None
    ):
        """
        Start the application - run until :py:func:`stop` is called.

        :keyword int port: Port to bind to.

        :keyword string address: Address to bind to.

        :keyword int blocking_log_threshold: Number of seconds the IO loop can
                                             be blocked for before Tornado
                                             will log an exception.
        """
        port = http_port or self.args.http_port
        addr = address or self.args.address
        limit = blocking_log_threshold or self.args.blocking_log_threshold

        self.logger.info("*** Starting application on %s:%s" % (addr, port))
        self.logger.info("***   Blocking log threshold set to: %s sec" % limit)

        self.listen(port, address=addr)

        instance = tornado.ioloop.IOLoop.instance()

        ### Set up the app, and catch any signals/exception that aren't handled
        ### elsewhere.
        try:
            self._setup_signals()

            instance.set_blocking_log_threshold(limit)

            instance.start()

        except KeyboardInterrupt:
            self.logger.info('*** Caught KeyboardInterrupt, exiting.')
            self.stop()

        except Exception:
            self.logger.exception('*** Caught an unhandled exception,'
                                  ' exiting.')
            self.stop(exit_code=1)

    def stop(self, exit_code=0):
        """
        Stop the application.

        :keyword int exit_code: Exit code to return to the parent process of
                                the application.
        """
        self.logger.info('*** Shutting down.')

        ### Any clean up can be done here
        tornado.ioloop.IOLoop.instance().stop()
        sys.exit(exit_code)

    def _setup_signals(self):
        """
        Set up signal handlers for the signals we care about.
        """
        ### add more handlers here if desired
        signal.signal(signal.SIGTERM, self._signal_stop)

    def _signal_stop(self, sig, frame):
        """
        Call self.stop() based on a signal
        """
        ### There doesn't seem to be a way to conver the signal (int)
        ### to it's name equivalent like, SIGTERM :(

        ### add logic on behaviour based on signal numbers here if desired
        self.logger.info("*** Received signal: %s" % sig)
        self.stop()


### Run the application stand alone, this is for testing purposes only
if __name__ == '__main__':
    app = Application(name='test_app', endpoint='/test')
    app.start()
