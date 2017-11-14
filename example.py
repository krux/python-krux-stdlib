#!/usr/bin/env python

import krux.cli


class ExampleLoggingApp(krux.cli.Application):
    """
    This class gets a few things for free; not least of which:
      * a command-line option parser
      * a logger
      * a stats dispatcher
      * a context manager, which cleans up after us,
        including deleting the lock file, if one was created.
    """
    def __init__(
        self,
        name,
        parser=None,
        logger=None,
        lockfile=False,
        syslog_facility=krux.cli.DEFAULT_LOG_FACILITY,
        log_to_stdout=True,
        parser_args=None,
    ):
        # The above method signature matches that of the parent, krux.cli.Application.__init__()
        super(ExampleLoggingApp, self).__init__(
            name=name,
            parser=parser,
            logger=logger,
            lockfile=lockfile,
            syslog_facility=syslog_facility,
            log_to_stdout=log_to_stdout,
            parser_args=parser_args,
        )

        # If you have command line arguments, this is when you want
        # to get retrieve & store them. super().__init__() will have stored them
        # self.args for us. The only place we want to read from self.args
        # is here in our __init__().
        self.bit_bucket_kg = self.args.bit_bucket_kg
        self.has_headlight_fluid = self.args.has_headlight_fluid

        # Do any other initialization tasks here
        pass

    # If your app wants to add its own command line arguments, do it here.
    # If not, then you don't need to create this method.
    def add_cli_arguments(self, parser):
        super(ExampleLoggingApp, self).add_cli_arguments(parser)

        # See the docstring & comments in get_group()
        group = krux.cli.get_group(self.parser, self.name)
        # Build arguments as you would with ArgumentParser
        # https://docs.python.org/2.7/library/argparse.html
        group.add_argument(
            '--bit-bucket-kg',
            default=5,
            help='Bit bucket weight in kg.',
        )
        group.add_argument(
            '-f', '--has-headlight-fluid',
            default=False,
            action='store_true',
            help='Contains sufficient headlight fluid.',
        )

    def run(self):
        """
        Trivial example of calling at least one thing.
        """
        print('The bit bucket weighs {} kg.'.format(self.bit_bucket_kg))
        if self.has_headlight_fluid:
            print('We have enough headlight fluid.')
        else:
            print('We could use more headlight fluid.')
        # the default log level is "warn" so you won't see these uness
        # you pass in --log-level from the command line
        self.logger.debug("this is a debug level message")
        self.logger.info("this is a info level message")


def main():
    # instantiate your application class.

    # the 'name' parameter is just a string/name for your script. It should be unique in your environment,
    # because stats will be emitted to statsd with that as part of the stat name.

    # the syslog_facility parameter being set changes where logs get sent to;
    # the default is to print them out to the console; setting a syslog facility
    # means messages will go to syslog with the named facility and called severity;
    # your local syslog config will need to route those messages to a file or remote syslog.

    app = ExampleLoggingApp('testloggingapp', syslog_facility='local0')

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
