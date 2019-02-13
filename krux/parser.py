# -*- coding: utf-8 -*-
#
# © 2013-2017 Salesforce.com, inc.
#

#
# Standard libraries
#
from __future__ import absolute_import
from os import environ

#
# Third party libraries
#
from argparse import ArgumentParser, _ArgumentGroup

#
# Internal libraries
#
from krux.logging import LEVELS, DEFAULT_LOG_LEVEL, DEFAULT_LOG_FACILITY
from krux.constants import (
    DEFAULT_STATSD_HOST,
    DEFAULT_STATSD_PORT,
    DEFAULT_STATSD_ENV,
    DEFAULT_LOCK_DIR,
)


def get_parser(
    logging=True,
    stats=True,
    lockfile=True,
    logging_stdout_default=True,
    *args,
    **kwargs
):
    # GOTCHA: KruxParser takes in a logger and a stats object. However, "stats" parameter is already defined
    #         as a boolean flag. Do not change the name of that parameter and break backward compatibility.
    # TODO: Update and clean up the parameter names so we can pass logger and stats into KruxParser.
    parser = KruxParser(*args, **kwargs)

    # standard logging arguments
    if logging:
        parser = add_logging_args(parser, logging_stdout_default)

    # standard stats arguments
    if stats:
        parser = add_stats_args(parser)

    # standard lockfile args
    if lockfile:
        parser = add_lockfile_args(parser)

    return parser


def add_logging_args(parser, stdout_default=True):
    """
    Add logging-related command-line arguments to the given parser.

    Logging arguments are added to the 'logging' argument group which is
    created if it doesn't already exist.

    :argument parser: parser instance to which the arguments will be added
    """
    group = get_group(parser=parser, group_name='logging')

    group.add_argument(
        '--log-level',
        default=DEFAULT_LOG_LEVEL,
        choices=LEVELS.keys(),
        env_var='LOG_LEVEL',
        help='Verbosity of logging.'
    )
    group.add_argument(
        '--log-file',
        default=None,
        env_var='LOG_FILE',
        help='Full-qualified path to the log file',
    )

    group.add_argument(
        '--no-syslog-facility',
        dest='syslog_facility',
        action='store_const',
        default=DEFAULT_LOG_FACILITY,
        const=None,
        env_var=False,
        add_default_help=False,
        help='disable syslog facility',
    )
    group.add_argument(
        '--syslog-facility',
        default=DEFAULT_LOG_FACILITY,
        env_var='SYSLOG_FACILITY',
        help='syslog facility to use',
    )
    #
    # If logging to stdout is enabled (the default, defined by the log_to_stdout arg
    # in __init__(), we provide a --no-log-to-stdout cli arg to disable it.
    #
    # If our calling script or subclass chooses to disable stdout logging by default,
    # we instead provide a --log-to-stdout arg to enable it, for debugging etc.
    #
    # This is particularly useful for Icinga monitoring scripts, where we don't want
    # logging info to reach stdout during normal operation, because Icinga ingests
    # everything that's written there.
    #
    # TODO: With the environment variable support, this use case should be handled
    #       via the environment variable. Consider removing this in v3.0
    if stdout_default:
        group.add_argument(
            '--no-log-to-stdout',
            dest='log_to_stdout',
            default=True,
            action='store_false',
            env_var=False,
            help='Suppress logging to stdout/stderr',
        )
    else:
        group.add_argument(
            '--log-to-stdout',
            default=False,
            action='store_true',
            env_var=False,
            help='Log to stdout/stderr -- useful for debugging!',
        )

    return parser


def add_stats_args(parser):
    """
    Add stats-related command-line arguments to the given parser.

    :argument parser: parser instance to which the arguments will be added
    """
    group = get_group(parser=parser, group_name='stats')

    group.add_argument(
        '--stats',
        default=False,
        action='store_true',
        env_var='STATS',
        help='Enable sending statistics to statsd.'
    )
    group.add_argument(
        '--stats-host',
        default=DEFAULT_STATSD_HOST,
        env_var='STATS_HOST',
        help='Statsd host to send statistics to.'
    )
    group.add_argument(
        '--stats-port',
        default=DEFAULT_STATSD_PORT,
        env_var='STATS_PORT',
        help='Statsd port to send statistics to.'
    )
    group.add_argument(
        '--stats-environment',
        default=DEFAULT_STATSD_ENV,
        env_var='STATS_ENVIRONMENT',
        help='Statsd environment.'
    )

    return parser


def add_lockfile_args(parser):
    group = get_group(parser=parser, group_name='lockfile')

    group.add_argument(
        '--lock-dir',
        default=DEFAULT_LOCK_DIR,
        env_var='LOCK_DIR',
        help='Dir where lock files are stored'
    )

    return parser


def get_group(parser, group_name, env_var_prefix=None):
    """
    Return an argument group based on the group name.

    This will return an existing group if it exists, or create a new one.

    :argument parser: :py:class:`python3:argparse.ArgumentParser` to
                      add/retrieve the group to/from.

    :argument group_name: Name of the argument group to be created/returned.
    """

    # We don't want to add an additional group if there's already a 'logging'
    # group. Sadly, ArgumentParser doesn't provide an API for this, so we have
    # to be naughty and access a private variable.
    groups = [g.title for g in parser._action_groups]

    if group_name in groups:
        group = parser._action_groups[groups.index(group_name)]
    else:
        group = parser.add_argument_group(title=group_name, env_var_prefix=env_var_prefix)

    return group


class KruxParser(ArgumentParser):
    def add_argument_group(self, *args, **kwargs):
        """
        Creates a KruxGroup object that wraps the argparse._ArgumentGroup and creates a nice group of arguments
        that should be considered together.

        :param env_var_prefix: Prefix to use for the environment variables support of this group. If set to None,
                               uses the title of the _ArgumentGroup that this is wrapping. If not set or set to False,
                               does not add any prefix. This argument MUST be a keyword argument.
        :type env_var_prefix: str | bool
        :param args: Ordered arguments passed directly to argparse._ArgumentGroup.__init__()
        :type args: list
        :param kwargs: Keyword arguments passed directly to argparse._ArgumentGroup.__init__()
        :type kwargs: dict
        :return: The created KruxGroup object
        :rtype: krux.parser.KruxGroup
        """
        # XXX: `title` and `description` are `_ArgumentGroup.__init__()`'s arguments. Sometimes, they come in as
        #      positional arguments. `KruxParser` must support that behaviour. Thus, we merge the two behaviours here.
        # XXX: Use `dict.pop()` so that we don't pass these twice.
        title = args[0] if len(args) > 0 else kwargs.pop('title', None)
        description = args[1] if len(args) > 1 else kwargs.pop('description', None)
        env_var_prefix = kwargs.pop('env_var_prefix', False)

        group = KruxGroup(container=self, title=title, description=description, env_var_prefix=env_var_prefix, **kwargs)
        self._action_groups.append(group)
        return group


class KruxGroup(_ArgumentGroup):
    HELP_ENV_VAR = "(env: {key})"
    HELP_DEFAULT = "(default: {default})"

    def __init__(self, env_var_prefix=False, **kwargs):
        """
        Creates a wrapper around argparse._ArgumentGroup that handles some help doc automation as well as environment
        variable fall back

        :param env_var_prefix: Prefix to use for the environment variables. If set to falsey, uses the title
                               of the _ArgumentGroup that this is wrapping.
        :type env_var_prefix: str
        :param args: Ordered arguments passed directly to krux.wrapper.Wrapper.__init__()
        :type args: list
        :param kwargs: Keyword arguments passed directly to krux.wrapper.Wrapper.__init__()
        :type kwargs: dict
        """
        # Call to the superclass to bootstrap.
        super(KruxGroup, self).__init__(**kwargs)

        if env_var_prefix:
            self._env_prefix = str(env_var_prefix) + '_'
        else:
            self._env_prefix = self.title + '_'

    def add_argument(self, *args, **kwargs):
        """
        Creates a CLI argument under this group based on the passed parameters.

        :param env_var: Name of the environment variable to use. If set to False or not
                        set, does not add any environment variable support. If set to None, uses the name of
                        the option and the env_var_prefix passed to the group to deduce a name.
        :type env_var: str | bool
        :param add_env_var_help: Whether to add the name of the environment variable to the help text. If set to False
                                 or if env_var is set to False, the help text is not appended.
        :type add_env_var_help: bool
        :param add_default_help: Whether to add the default value of the argument to the help text. If set to False
                                 or if the help text already includes it, it is not appended.
        :type add_default_help: bool
        :param args: Ordered arguments passed directly to argparse._ArgumentGroup.add_argument()
        :type args: list
        :param kwargs: Keyword arguments passed directly to argparse._ArgumentGroup.add_argument()
        :type kwargs: dict
        :return: Action class of this argument
        :rtype: argparse.Action
        """
        # Values that are used exclusively in this override
        env_var = kwargs.pop('env_var', False)
        add_env_var_help = kwargs.pop('add_env_var_help', True)
        add_default_help = kwargs.pop('add_default_help', True)

        # Values that are referenced in this override but also used in _ArgumentGroup
        old_default_value = kwargs.get('default', None)
        old_help_value = kwargs.get('help', '')
        help_text_list = [old_help_value]

        # There must be an argument defined and it must be prefixed. (i.e. This does not handle positional arguments.)
        is_optional_argument = (len(args) > 0 and args[0][0] in self.prefix_chars)

        # Modify the default value to rely on the environment variable
        if env_var is not False and is_optional_argument:
            # Find the first long-named option
            first_long = next((arg_name for arg_name in args if arg_name[1] in self.prefix_chars), None)

            # There must be a long name or environment variable support is explicitly turned off.
            if first_long is None:
                raise ValueError(
                    'You must either disable the environment variable fall back or provide a long name for the option'
                )

            if env_var is None:
                # Determine the key of the environment variable for this argument
                key = first_long.lstrip(self.prefix_chars)
                if not key:
                    raise ValueError(
                        'You must provide a valid name for the option'
                    )
                # TODO: Handle all of prefix_chars, not just '-' here
                key = (self._env_prefix + key).replace('-', '_').upper()
            else:
                key = env_var

            # Override the default value to use the environment variable
            #
            # @plathrop 2017.12.28-15:13: This used to be:
            #
            # kwargs['default'] = environ.get(key=key, failobj=kwargs.get('default', None))
            #
            # However, in python 3, they renamed the 'failobj' keyword
            # argument. To make this code compatible, the simplest
            # method is to pass in the arguments positionally.
            kwargs['default'] = environ.get(key, kwargs.get('default', None))

            # Add the environment variable to the help text
            if add_env_var_help:
                help_text_list.append(self.HELP_ENV_VAR.format(key=key))

        # Append the default value to the help text
        if add_default_help and is_optional_argument and "(default: " not in old_help_value:
            help_text_list.append(self.HELP_DEFAULT.format(default=old_default_value))

        kwargs['help'] = ' '.join(help_text_list)

        return super(KruxGroup, self).add_argument(*args, **kwargs)
