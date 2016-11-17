# -*- coding: utf-8 -*-
#
# © 2014 Krux Digital, Inc.
#
"""
Unit tests for the krux.io module.
"""
######################
# Standard Libraries #
######################
from __future__ import absolute_import
from unittest import TestCase
from logging import Logger

import re
import shlex
import shutil
import tempfile
import signal

#########################
# Third Party Libraries #
#########################
from nose.tools import assert_equal, assert_true, assert_false, raises
from mock import MagicMock, patch, call
import subprocess32

######################
# Internal Libraries #
######################

import krux.io


class TestApplication(TestCase):
    TIMEOUT_COMMAND = 'sleep 5'
    TIMEOUT_SECOND = 2
    TIMEOUT_SIGNAL = signal.SIGINT
    SHELL_INJECTION_BACKTICK = '`touch {0}/p0wn`'
    SHELL_INJECTION_PARENS = '$(touch {0}/p0wn)'
    SHELL_INJECTION_SEMICOLON = 'true; touch {0}/p0wn'
    QUOTED_FILE_NAME = '{0}/file name with spaces'

    def setUp(self):
        """
        Common test initialization
        """
        super(TestApplication, self).setUp()

        self.io = krux.io.IO()

        # Create a temporary directory; needed for the shell escape tests
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """
        krux.io initializion sets the expected attributes.
        """

        assert_true(self.io.logger)
        assert_true(self.io.stats)

    def test_cmd_true(self):
        """ Test return code from successful command """
        cmd = self.io.run_cmd( command = 'true' )

        assert_true(cmd.ok)
        assert_equal(cmd.returncode, 0)

        ### additional tests, just so we have 'm at least once
        assert_equal(cmd.command, 'true')

    def test_cmd_as_list(self):
        """ Commands can be provided as a list """
        cmd = self.io.run_cmd( command = ['true'] )

        assert_true(cmd.ok)
        assert_equal(cmd.returncode, 0)

    def test_cmd_false(self):
        """ Test return code from failing command """
        cmd = self.io.run_cmd( command = 'false' )

        assert_false(cmd.ok)
        assert_equal(cmd.returncode, 1)

    @raises(krux.io.RunCmdError)
    def test_cmd_exception(self):
        """ Test we can raise exceptions """
        cmd = self.io.run_cmd( command = 'false', raise_exception = True )

    def test_cmd_stdout(self):
        """ Make sure we can capture stdout """
        cmd = self.io.run_cmd( command = 'echo 42' )

        assert_true(cmd.ok)
        assert_equal(cmd.returncode, 0)
        assert_equal(''.join(cmd.stdout), '42')

    def test_cmd_filters(self):
        """ Strip out parts of the output, based on filters """

        filter = re.compile( '\d+' )
        cmd    = self.io.run_cmd( command = 'echo 42', filters = [ filter ] )

        assert_true(cmd.ok)
        assert_equal(cmd.returncode, 0)
        assert_false(len(cmd.stdout))

    def test_broken_input(self):
        """ Commands must be strings/buffers, not objects - test for exceptions """

        cmd = self.io.run_cmd( command = self )

        ### parsing failed, so the command is not ok, but there's no return
        ### code set for it, but exceptions are filled
        assert_false(cmd.ok)
        assert_true(cmd.exception)
        assert_equal(cmd.returncode, krux.io.RUN_COMMAND_EXCEPTION_EXIT_CODE)

        ### but these are all not set
        assert_false(len(cmd.stdout))
        assert_false(len(cmd.stderr))

    def test_timeout(self):
        """
        run_cmd re-throws a TimeoutExpired error from subprocess upon timing out
        """
        # Mocking the logger to check for calls later
        mock_logger = MagicMock(
            spec=Logger,
            autospec=True,
        )

        # Mocking the subprocess module
        timeout_error = subprocess32.TimeoutExpired(self.TIMEOUT_COMMAND, self.TIMEOUT_SECOND)
        mock_process = MagicMock(
            communicate=MagicMock(
                side_effect=[timeout_error, ('', '')]
            ),
        )
        mock_popen = MagicMock(
            return_value=mock_process
        )

        with patch('krux.io.subprocess.Popen', mock_popen):
            self.io = krux.io.IO(logger=mock_logger)
            cmd = self.io.run_cmd(
                command = self.TIMEOUT_COMMAND,
                timeout = self.TIMEOUT_SECOND,
                timeout_terminate_signal = self.TIMEOUT_COMMAND
            )

            # Check to make sure the command has failed with expected exception
            assert_false(cmd.ok)
            assert_true(cmd.exception)
            assert_true(isinstance(cmd.exception, subprocess32.TimeoutExpired))
            assert_equal(cmd.returncode, krux.io.RUN_COMMAND_EXCEPTION_EXIT_CODE)

        # Check to make sure error handling is done correctly and process is sent the given signal
        mock_process.communicate.assert_has_calls( [ call( timeout = self.TIMEOUT_SECOND ), call() ] )
        mock_process.send_signal.assert_called_once_with( self.TIMEOUT_COMMAND )

        # Check to make sure the error is logged
        mock_logger.critical.assert_called_once_with('Command failed: %s', timeout_error)

    def test_shell_injection_backtick(self):
        """
        Test that a command with backticks in it fails to run.
        """
        cmd = self.io.run_cmd(
            command=['ls', self.SHELL_INJECTION_BACKTICK],
        )

        assert_false(cmd.ok)

    def test_shell_injection_parens(self):
        """
        Test that a command with a $() subcommand in it fails to run.
        """
        cmd = self.io.run_cmd(
            command=['ls', self.SHELL_INJECTION_PARENS],
        )

        assert_false(cmd.ok)

    def test_shell_injection_semicolon(self):
        """
        Test that a command with a $() subcommand in it fails to run.
        """
        cmd = self.io.run_cmd(
            command=['ls', self.SHELL_INJECTION_SEMICOLON],
        )

        assert_false(cmd.ok)

    def test_quoted_file_names(self):
        """
        Test that when we pass in a file name that needs to be quoted, that we can
        use that filename in a command.
        """

        filename = self.QUOTED_FILE_NAME.format(self.temp_dir)
        filehandle = open(filename, 'w')
        filehandle.write("hello world")
        filehandle.close()

        cmd = self.io.run_cmd(
            command='rm -f {0}'.format(filename)
        )

        assert_true(cmd.ok)
