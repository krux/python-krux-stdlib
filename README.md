# krux-stdlib

[![Code Climate](https://codeclimate.com/github/krux/python-krux-stdlib/badges/gpa.svg)](https://codeclimate.com/github/krux/python-krux-stdlib)

https://staticfiles.krxd.net/foss/docs/pypi/krux-stdlib/

## Using python-krux-stdlib

1.  Add the Krux pip repository and python-krux-stdlib to the top of
    your project's `requirements.pip` file:

        ### Optional - also available on PyPi
        --extra-index-url https://staticfiles.krxd.net/foss/pypi/
        krux-stdlib==2.0.0

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

1.  Clone the repository.

        git clone git@github.com:krux/python-krux-stdlib.git ~/Projects/krux-stdlib

2.  Set up a virtual environment.

        mkdir -p ~/.virtualenv/krux-stdlib && virtualenv ~/.virtualenv/krux-stdlib

3.  Activate the virtual environment.

        source ~/.virtualenv/krux-stdlib/bin/activate

4.  Install the requirements.

        cd ~/Projects/krux-stdlib; pip install -r requirements.pip

5.  Hack away! Make sure to add unit tests.

6.  Make sure you document everything. You can preview the generated
    documentation by running:

        make html

    in the `doc` subdirectory. Then open `doc/github/html/index.html`
    in your favorite browser.

7.  To cut a release, update the VERSION in `setup.py`, merge to the
    `release` branch, and push to GitHub. Jenkins will build and
    upload the new version to the Krux python repository, as well as
    tagging the release in git and updating the documentation.

    Note: To set this kind of workflow up for your own projects, clone
    the python-krux-stdlib Jenkins job :-)
