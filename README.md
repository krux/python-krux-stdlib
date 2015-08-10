# krux-stdlib

## Using python-krux-stdlib

1.  Add the Krux pip repository and python-krux-stdlib to the top of
    your project's `requirements.pip` file:

```unix
### Optional - also available on PyPi
--extra-index-url https://staticfiles.krxd.net/foss/pypi/
krux-stdlib==1.2.0
```
2.  Code up your app. First, define your class to inherit from krux.cli.Application. In the `__init__()` method, 
initialize the superclass, passing in whatever parameters you need. Minimally:
```python
    class TestLoggingApp( krux.cli.Application ):
        def __init__(self):
            super(TestLoggingApp, self).__init__(name = 'testloggingapp', syslog_facility='local0')
```

2. Now you are ready to define any methods you might need under your Application() subclass:
```python
def foo_things(self):
    self.logger.debug("just called foo_things()")
```
3. Finally, call the whole kit from `main()`:
```python
def main():
    app = TestLoggingApp()
    app.logger.debug("this is a debug level message")
    app.foo_things()
```

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

7.  To cut a release, update the VERSION in `setup.py`, merge to the
    `release` branch, and push to GitHub. Jenkins will build and
    upload the new version to the Krux python repository, as well as
    tagging the release in git.

    Note: To set this kind of workflow up for your own projects, clone
    the python-krux-stdlib Jenkins job :-)
