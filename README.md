# krux-stdlib

[![Code Climate](https://codeclimate.com/github/krux/python-krux-stdlib/badges/gpa.svg)](https://codeclimate.com/github/krux/python-krux-stdlib)

## Using python-krux-stdlib

1.  Add the Krux pip repository and python-krux-stdlib to the top of
    your project's `requirements.pip` file:

        ### Optional - also available on PyPi
        --extra-index-url https://staticfiles.krxd.net/foss/pypi/
        krux-stdlib==2.1.1

2.  Code up your app. First, define your class to inherit from
    krux.cli.Application. In the `__init__()` method, initialize the
    superclass, passing in whatever parameters you need. Minimally:

        class TestLoggingApp( krux.cli.Application ):
            def __init__(self):
                super(TestLoggingApp, self).__init__(name='testloggingapp', syslog_facility='local0')

3. Now you are ready to define any methods you might need under your
   Application() subclass:

        def foo_things(self):
            self.logger.debug("just called foo_things()")

4. Finally, call the whole kit from `main()`:

        def main():
            app = TestLoggingApp()
            app.logger.debug("this is a debug level message")
            app.foo_things()

## Developing python-krux-stdlib

### Prerequisites:
- Python 3.6 or above.
- pipenv

1.  Clone the repository.

        git clone git@github.com:krux/python-krux-stdlib.git && cd python-krux-stdlib

2.  Set up a virtual environment.

        pipenv install --develop

3.  Hack away! Make sure to add unit tests.

4.  Run tests.

        pipenv run python setup.py test

5.  To cut a release, update the VERSION in `krux/__init__.py` and push to GitHub.
    Jenkins will build and upload the new version to the Krux python repository,
    as well as tagging the release in git.
