# -*- coding: utf-8 -*-
#
# © 2013 Krux Digital, Inc.
#
"""
Unit tests for krux.tornado.Application
"""

######################
# Standard Libraries #
######################
from __future__ import absolute_import
from unittest   import TestCase

#########################
# Third Party Libraries #
#########################
from argparse   import ArgumentParser
from mock       import Mock, mock_open, patch
from nose.tools import assert_equal, assert_true

######################
# Internal Libraries #
######################
from krux.tornado          import Application
from krux.tornado.cli      import get_parser
from krux.tornado.handlers import ErrorHandler, StatusHandler


### No matter what the cli options to the test, assume none were given to the app
DEFAULT_ARGS = get_parser().parse_args([])


@patch('krux.cli.get_parser')
def test_setup(mock_parser):
    """
    Verify that basic set up is done
    """

    ### run with no args
    mock_parser.return_value.parse_args.return_value = DEFAULT_ARGS

    app = Application(name = 'test_app', endpoint = '/test')

    assert_true(app)



class TestApplication(TestCase):
    """
    Tests for krux.tornado.application.Application.
    """
    def setUp(self):
        """
        Setup steps for each Application test.
        """
        # Simple attributes used by the tests
        self.endpoint = '/tests'

        # Mock the command-line parser so it doesn't attempt to parse the
        # command line of our test runner.
        self.parser_patch = patch(
            'krux.tornado.cli.get_parser', spec = ArgumentParser
        )
        self.mock_parser = self.parser_patch.start()

        # Set up the mock parser to behave as if defaults were used.
        self.mock_parser.return_value.parse_args.return_value = DEFAULT_ARGS

    def tearDown(self):
        """
        Teardown steps for each Application test.
        """
        self.parser_patch.stop()

    def test_default_handlers(self):
        """
        Application default handlers are correctly added.
        """
        app = Application(name = __name__, endpoint = self.endpoint)

        # app.handlers[0][1] gets us the URLSpec objects, which is what we
        # actually care about.
        assert_equal(len(app.handlers[0][1]), 2)
        status_handler, error_handler = app.handlers[0][1]

        # Check the status handler
        assert_equal(
            status_handler.regex.pattern, r'%s/__status/?$' % self.endpoint
        )
        assert_equal(
            status_handler.handler_class, StatusHandler
        )

        # Check the error handler
        assert_equal(error_handler.regex.pattern, r'/.*/?$')
        assert_equal(
            error_handler.handler_class, ErrorHandler
        )

    def test_class_handlers(self):
        """
        Application handlers defined on the class are used
        """
        handler_spec = (r'/handler$', ErrorHandler)
        class FakeApplication(Application):
            # Handlers defined as a class attribute
            app_handlers = [handler_spec]

        app = FakeApplication(name = __name__, endpoint = self.endpoint)

        # app.handlers[0][1] gets us the URLSpec objects, which is what we
        # actually care about. The first item in that list should be the
        # handler defined on the class.
        handler = app.handlers[0][1][0]

        assert_equal(handler.regex.pattern, handler_spec[0])
        assert_equal(handler.handler_class, handler_spec[1])

    def test_instance_handlers(self):
        """
        Application handlers defined on the instance are used
        """
        handler_spec = (r'/handler$', ErrorHandler)
        class FakeApplication(Application):
            def __init__(self, *args, **kwargs):
                # Handlers defined as an instance attribute
                self.app_handlers = [handler_spec]
                super(FakeApplication, self).__init__(*args, **kwargs)

        app = FakeApplication(name = __name__, endpoint = self.endpoint)

        # app.handlers[0][1] gets us the URLSpec objects, which is what we
        # actually care about. The first item in that list should be the
        # handler defined on the class.
        handler = app.handlers[0][1][0]

        assert_equal(handler.regex.pattern, handler_spec[0])
        assert_equal(handler.handler_class, handler_spec[1])

    def test_get_version_from_file(self):
        """
        Application.get_version reads the version from a file named VERSION.
        """
        module      = 'krux.tornado.application'
        version     = '1.0.0\n'
        version2    = '2.0.0\n'
        mocked_open = mock_open(read_data = version)
        mock_handle = mocked_open()

        mock_handle.readline.return_value = version

        with patch('%s.os.path.exists' % module, return_value = True):
            with patch('%s.open' % module, mocked_open, create = True):
                app = Application(name = __name__, endpoint = self.endpoint)

        assert_equal(app.version, version.strip())

        # Change the value stored in our mock version file
        mock_handle.readline.return_value = version

        with patch('%s.os.path.exists' % module, return_value = True):
            with patch('%s.open' % module, mocked_open, create = True):
                # Even though the version file changed, our running
                # application did not change, so it should still be
                # reporting the old version.
                assert_equal(app.version, version.strip())

    @patch('krux.tornado.application.git.Repo', autospec = True)
    def test_get_version_from_git(self, mock_repo):
        """
        Application.get_version reads version from git if VERSION file absent.
        """
        module = 'krux.tornado.application'
        commit = 'deadbeef'

        mock_repo.return_value.commit.return_value = commit

        results = [False, True]
        def exists_results(*args):
            return results.pop(0)

        mock_exists = Mock(side_effect = exists_results)
        with patch('%s.os.path.exists' % module, mock_exists):
            app = Application(name = __name__, endpoint = self.endpoint)

        assert_equal(app.version, commit)


    @patch('krux.tornado.application.git.Repo', autospec = True)
    def test_get_version_no_version(self, mock_repo):
        """
        Application.get_version reads version from git if VERSION file absent.
        """
        module = 'krux.tornado.application'

        results = [False, False]
        def exists_results(*args):
            return results.pop(0)

        mock_exists = Mock(side_effect = exists_results)
        with patch('%s.os.path.exists' % module, mock_exists):
            app = Application(name = __name__, endpoint = self.endpoint)

        assert_equal(app.version, None)
