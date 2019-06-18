# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#
"""
This module provides tools for handling IO operations, like running
external commands.

Usage::

        from krux.io import IO
        io  = IO()
        cmd = io.run_cmd( command = 'echo 42' )

        if cmd.ok:
          ....
        else:
          print cmd.stderr



"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from __future__ import print_function
from builtins import object
from past.builtins import basestring
import shlex
import signal
import sys
import os
import re

#########################
# Third Party Libraries #
#########################

if os.name == 'posix' and sys.version_info[0] < 3:
    # For Python 2.*, use the backported subprocess
    import subprocess32 as subprocess
else:
    import subprocess

######################
# Internal Libraries #
######################

from krux.util import hasmethod

import krux.logging
import krux.cli
import krux.stats

RUN_COMMAND_EXCEPTION_EXIT_CODE = 256


class RunCmdError(Exception):
    pass


class IORunCmd(object):
    """
    Krux base class running command line programs

    This should only ever be accessed via IO().run_cmd()
    """

    def __init__(self, logger, stats):
        self.___logger = logger
        self.___stats  = stats

        ### properties of the finished command:
        self.command    = None
        self.returncode = 0
        self.ok         = True
        self.stdout     = [ ]
        self.stderr     = [ ]
        self.exception  = None

    def run(self, command, filters=None, timeout=None, timeout_terminate_signal=signal.SIGTERM):
        log     = self.___logger
        stats   = self.___stats

        ### for bookkeeping purposes
        self.command = command

        log.debug('About to run: %s' % command)

        ### figure out if we've been passed a regex or a string for filtering
        def is_regex(thing):
            return hasattr(thing, 'pattern') and hasmethod(thing, 'search')

        if filters:
            filters = [is_regex(f) and f or re.compile(f) for f in filters]
        else:
            filters = []

        log.debug('Applying output filters: %s' % [r.pattern for r in filters])

        # if the command is a string, split it using shlex; which correctly handles quoted args like:
        #  cat "/var/log/foo bar.log" /var/log/baz\ .log
        log.debug('command isinstance basestring: %s', isinstance(command, basestring))
        if isinstance(command, basestring):
            command = shlex.split(command)

        try:
            process = subprocess.Popen(
                command,
                stderr = subprocess.PIPE,
                stdout = subprocess.PIPE,
                shell = False
            )

            # Note that using communicate() buffers all output in memory and can
            # hang if the buffer is filled.
            try:
                stdout, stderr = process.communicate(timeout = timeout)
            except subprocess.TimeoutExpired:
                process.send_signal(timeout_terminate_signal)
                stdout, stderr = process.communicate()
                raise

            ### set the bookkeeping variables.
            ### the exit code is set on the process; communicate doesn't provide
            ### the exit code, just the outputs. So check it here. For details:
            ### https://docs.python.org/3.3/library/subprocess.html#subprocess.Popen.communicate
            self.returncode = process.returncode
            self.ok         = False if self.returncode > 0 else True

            ### print diagnostics if needed
            mapping = {
                # label             log function    output string   return value
                'Command output': [ log.info,       stdout,         self.stdout ],
                'Command errors': [ log.warning,    stderr,         self.stderr ],
            }

            for label, outputs in list(mapping.items()):

                ### there was output
                if len(outputs[1]):

                    for b in outputs[1].splitlines():
                        s = b.decode("utf-8")
                        ignore = False

                        for r in filters:
                            ### but you wanted it filtered
                            if r.search(s):
                                log.debug('line "%s" matches "%s"' % (s, r.pattern))
                                ignore = True
                        ### not filtered - store the filtered output in the object,
                        ### so caller can inspect them
                        ignore or outputs[2].append(s)

                    ### print the entire output buffer
                    len(outputs[2]) and outputs[0]('%s: %s' % (label, "\n".join(outputs[2])))

            if not self.ok:
                return False

            ### if we got here, everything's fine
            return True

        ### The command failed
        except Exception as err:
            stats.incr('error.run_cmd')
            log.critical('Command failed: %s', err)

            ### we're definitely in trouble, and don't know how
            ### far we've gotten, so just set them all again
            self.exception  = err
            self.ok         = False
            ### 0-255 is Normal Exitcodes
            self.returncode = self.returncode or RUN_COMMAND_EXCEPTION_EXIT_CODE

            return False


class IO(object):
    """
    Krux base class for IO interactions
    """

    def __init__(self, logger=None, stats=None):
        """
        Wraps :py:class:`object` and provides IO routines

        :keyword logger: The logger utility. Defaults to
        :py:func:`logging.get_logger <krux.logging.get_logger>`

        :keyword stats: The stats utility. Defaults to
        :py:func:`cli.get_stats <krux.cli.get_stats>`
        """

        ### You shouldn't make us get the default ones, but instead use
        ### this via krux.cli which will have a fully instantiated object
        self.__name = krux.cli.get_script_name()
        self.logger = logger or krux.logging.get_logger(name = self.__name)
        self.stats  = stats  or krux.stats.get_stats( prefix = 'io.%s' % self.__name )


    def run_cmd(self, raise_exception = False, *args, **kwargs):
        """
        Dispatches to :py:class:`IORunCmd` run() method. This is the
        preferred way to run an external command.

        :keyword command: The command to run, either as a list or as a string.
        If the latter, it will be split on whitespace. Required argument.

        :keyword filters: list of output filters to apply to stdout/stderr before
        capturing or logging it. Filters can be strings or regular expressions.

        :keyword raise_exception: If an error occurs, a :py:class:`RunCmdError`
        exception will be thrown. Defaults to False.

        """

        cmd = IORunCmd( logger = self.logger, stats = self.stats )

        ### true/false on success/failure
        rv = cmd.run(*args, **kwargs)

        ### you want us to just throw exception?
        if raise_exception and not rv:
            raise RunCmdError(
                "Failed command '%s' (%d): %s" % \
                (cmd.command, cmd.returncode, ' '.join(cmd.stderr))
            )

        ### return the IORunCmd object, so it can be inspected
        return cmd


"""
Quick testing routine when running stand alone
"""
def main():
    logger = krux.logging.get_logger( name = 'io-test-app', level = 'debug' )

    io = IO( logger = logger )

    cmd = io.run_cmd( command = "false", raise_exception = False )

    print(cmd.ok)
    print(cmd.returncode)
    print(cmd.stdout)
    print(cmd.stderr)



### Run the application stand alone
if __name__ == '__main__':
    main()
