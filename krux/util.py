# Copyright 2013-2020 Salesforce.com, inc.
"""
Miscellaneous utilities that don't have a better home.
"""
from __future__ import generator_stop

from datetime import datetime, timedelta
from functools import partial, wraps
from typing import Any, Callable, Mapping, Sequence, Union


def hasmethod(obj, method):
    """
    Return True if OBJ has an attribute named METHOD and that attribute is
    callable. Otherwise, return False.

    :argument object obj: an object
    :argument string method: the name of the method
    """
    return callable(getattr(obj, method, None))


def get_percentage(value, total, decimal_points=4):
    """
    @param value: value in int or double
    @param total: total in int or double
    @param decimal_points: how many decimal points for return result
    @return: the percentage: value of total.
    """
    return round(
        divide_or_zero(value * 1.0, total * 1.0, 0.0) * 100.0,
        decimal_points
    )


def divide_or_zero(numerator, denominator, default=None):
    """
    @param numerator: numerator
    @param denominator: denominator
    @param default: default return
    @return: numerator // denominator
    """
    return numerator // denominator if denominator != 0 else default


def flatten(lst):
    """
    Flattens a mixture of lists and objects into a one-dimensional list

    https://rosettacode.org/wiki/Flatten_a_list#Generative

    :param lst: :py:class:`list` List to flatten
    """
    for x in lst:
        if isinstance(x, list):
            for y in flatten(x):
                yield y
        else:
            yield x


_args_kwargs_delimiter = object()  # A unique hashable object.


def _function_args_hash(args: Sequence = None,
                        kwargs: Mapping = None,
                        _separator=object(),
                        ) -> int:
    """Make a hash key out of the args & kwargs for a function call."""
    _args = tuple(args) if args else ()
    _kwargs = tuple(kwargs.items()) if kwargs else ()
    return hash(_args + (_args_kwargs_delimiter,) + _kwargs)


def cache(cached_function: Callable = None, *, expire_seconds: Union[float, int] = None) -> Callable:
    """Caching decorator with optional expiration in seconds.

    Example:
        >>> from urllib.request import urlopen
        >>> @cache(expire_seconds=60)
        ... def get_page(url):
        ...     with urlopen(url) as r:
        ...     return r.read().decode()
    """
    if cached_function is None:
        return partial(cache, expire_seconds=expire_seconds)

    _cached_function = cached_function  # type: Callable
    del cached_function
    expire_delta = timedelta(seconds=expire_seconds) if expire_seconds is not None else timedelta.max
    items = {}  # type: dict

    @wraps(_cached_function)
    def wrapper(*args: Sequence, **kwargs: Mapping) -> Any:
        now = datetime.now()
        key = _function_args_hash(args, kwargs)
        item = items[key] if key in items else None
        if item and now < item['expiration']:
            return item['value']
        else:
            value = _cached_function(*args, **kwargs)
            expiration = now + expire_delta if expire_delta != timedelta.max else datetime.max
            items[key] = {'value': value, 'expiration': expiration}
            return value

    return wrapper
