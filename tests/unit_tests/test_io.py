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

import re
import sys

#########################
# Third Party Libraries #
#########################
from nose.tools import assert_equal, assert_true, assert_false, raises

######################
# Internal Libraries #
######################

import krux.io


class TestApplication(TestCase):
    def setUp(self):
        """
        Common test initialization
        """
        super(TestApplication, self).setUp()

        self.io = krux.io.IO()

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



