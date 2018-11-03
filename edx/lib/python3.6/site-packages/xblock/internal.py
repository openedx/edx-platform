"""
Internal machinery used to make building XBlock family base classes easier.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import inspect

import six


class LazyClassProperty(object):
    """
    A descriptor that acts as a class-level @lazy.

    That is, it behaves as a lazily loading class property by
    executing the decorated method once, and then storing the result
    in the class __dict__.
    """
    def __init__(self, constructor):
        self.__constructor = constructor
        self.__cache = {}
        functools.wraps(self.__constructor)(self)

    def __get__(self, instance, owner):
        if owner not in self.__cache:
            # If __constructor iterates over members, then we don't want to call it
            # again in an infinite loop. So, preseed the __cache with None.
            self.__cache[owner] = None
            self.__cache[owner] = self.__constructor(owner)
        return self.__cache[owner]


class_lazy = LazyClassProperty  # pylint: disable=invalid-name


class NamedAttributesMetaclass(type):
    """
    A metaclass which adds the __name__ attribute to all Nameable attributes
    which are attributes of the instantiated class, or of its baseclasses.
    """
    def __new__(mcs, name, bases, attrs):
        # Iterate over the attrs before they're bound to the class
        # so that we don't accidentally trigger any __get__ methods
        for attr_name, attr in six.iteritems(attrs):
            if Nameable.needs_name(attr):
                attr.__name__ = attr_name

        # Iterate over all of the base classes, so that we can add
        # names to any mixins that don't include this metaclass, but that
        # do include Nameable attributes
        for base in bases:
            for attr_name, attr in inspect.getmembers(base, Nameable.needs_name):
                attr.__name__ = attr_name

        return super(NamedAttributesMetaclass, mcs).__new__(mcs, name, bases, attrs)


class Nameable(object):
    """
    A base class for class attributes which, when used in concert with
    :class:`.NamedAttributesMetaclass`, will be assigned a `__name__`
    attribute based on what class attribute they are bound to.
    """
    if six.PY2:
        __slots__ = ('__name__',)
    __name__ = None

    @staticmethod
    def needs_name(obj):
        """
        Return True if `obj` is a :class:`.Nameable` object that
        hasn't yet been assigned a name.
        """
        return isinstance(obj, Nameable) and obj.__name__ is None
