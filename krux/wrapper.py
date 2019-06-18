# -*- coding: utf-8 -*-
#
# © 2017 Krux Digital, Inc.
#

#
# Standard libraries
#
from __future__ import absolute_import
from abc import ABCMeta

#
# Third party libraries
#
from future.utils import with_metaclass

#
# Internal libraries
#
from krux.object import Object


class Wrapper(with_metaclass(ABCMeta, Object)):
    # Wrapper is an abstract class and not to be instantiated directly. It should be used by being inherited
    def __init__(self, wrapped, *args, **kwargs):
        # Call to the superclass to bootstrap.
        super(Wrapper, self).__init__(*args, **kwargs)

        self._wrapped = wrapped

    def _get_wrapper_function(self, func):
        """
        Returns a function to be called given a function from the wrapped class. Override this function to generate
        a default wrapper around the function.

        :example:
            >>>class Foo(Wrapper):
            >>>    def _get_wrapper_function(self, func):
            >>>        def logged_function(*args, **kwargs):
            >>>            self._logger.debug("Calling function %s with args %s and kwargs %s", func.__name__, args, kwargs)
            >>>            return func(*args, **kwargs)
            >>>        return logged_function
            >>>
            >>>foo = Foo(list)
            >>>foo.append(1)
            >>># Debug log: Calling function append with args [1] and kwargs {}

        :param func:
        :type func: function
        :return: The function to be executed
        :rtype: function
        """
        return func

    def __getattr__(self, name):
        """
        Finds and returns the attribute defined in the wrapped class and not in the wrapper class.

        :param name: Name of the attribute
        :type name: str
        :return: Value of the attribute
        :rtype: Any
        """
        self._logger.debug("Attribute %s is not defined directly in this class. Looking up the wrapped object", name)

        # GOTCHA: This will throw AttributeError if name is not defined in self._wrapped. If the code got here, that
        #         means there is no extra code added around self._wrapped with the attribute named `name`.
        #         If self._wrapped also does not have an attribute named `name`, then it should fail with the same
        #         exception as if you did self._wrapped.`name`. Thus, the error is purposely not handled here.
        value = getattr(self._wrapped, name)

        if callable(value):
            self._logger.debug("Found function %s in the wrapped object", name)

            # Currently this wrapper function does not do anything, but leave a shell here for an ex
            return self._get_wrapper_function(value)
        else:
            self._logger.debug("Found value %s for the attribute %s in the wrapped object", value, name)
            return value