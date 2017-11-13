#!/usr/bin/env python

import krux.cli


class ExampleLoggingApp(krux.cli.Application):
    """
    This class gets a few things for free; not least of which:
      * a command-line option parser
      * a logger
    """
    def __init__(self, *args, **kwargs):
        # the 'name' parameter is just a string/name for your script. It should be unique in your environment,
        # because stats will be emitted to statsd with that as part of the stat name.

        # the syslog_facility parameter being set changes where logs get sent to;
        # the default is to print them out to the console; setting a syslog facility
        # means messages will go to syslog with the named facility and called severity;
        # your local syslog config will need to route those messages to a file or remote syslog.

        # A NOTE ON *args AND **kwargs: Our intent is to capture and pass on the arguments
        # to parent methods, which want to use them. This is one way. Another way
        # is to declare the arguments explicitly. There's a software maintenance cost to that, though:
        # if parameter changes are made to a ancestor method, it may require a change
        # to the descendant methods.
        super(ExampleLoggingApp, self).__init__(name='testloggingapp', syslog_facility='local0', *args, **kwargs)

    def run(self):
        """
        Trivial example of calling at least one thing.
        """
        # the default log level is "warn" so you won't see these uness
        # you pass in --log-level from the command line
        self.logger.debug("this is a debug level message")
        self.logger.info("this is a info level message")


def main():
    # instantiate your application class
    app = ExampleLoggingApp()

    # app.context() makes sure the exceptions are logged, if any, exit hooks are handled (i.e. lock files),
    # and exit code is set properly.
    with app.context():
        # go ahead and call whatever methods you have defined under your app; .logger is
        # provided by the Krux standard library. calling logger with each available log level
        # might help you diagnose/tune your local syslog config; you can also over-ride the
        # class' syslog_facility as configured above with the --syslog-facility argument.
        app.run()
        app.logger.warn("this is a warning level message")
        app.logger.error("this is a error level message")
        app.logger.critical("this is a critical level message")


if __name__ == '__main__':
    main()
