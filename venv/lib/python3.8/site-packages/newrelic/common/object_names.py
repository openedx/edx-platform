# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module implements functions for deriving the full name of an object.

"""

import sys
import types
import inspect
import functools

from newrelic.packages import six

if six.PY2:
    import exceptions
    _exceptions_module = exceptions
elif six.PY3:
    import builtins
    _exceptions_module = builtins
else:
    _exceptions_module = None

# Object model terminology for quick reference.
#
# class:
#
#   __module__:
#     name of module in which this class was defined
#
# method:
#
#   __name__:
#     name with which this method was defined
#   __qualname__:
#     qualified name with which this method was defined
#   im_class:
#     class object that asked for this method
#   im_func or __func__:
#     function object containing implementation of method
#   im_self or __self__:
#     instance to which this method is bound, or None
#
# function:
#
#   __name__:
#     name with which this function was defined
#   __qualname__:
#     qualified name with which this function was defined
#   func_name:
#     (same as __name__)
#
# descriptor:
#
#   __objclass__:
#     class object that the descriptor is bound to
#
# builtin:
#
#   __name__:
#     original name of this function or method
#   __self__:
#     instance to which a method is bound, or None

def _module_name(object):
    mname = None

    # For the module name we first need to deal with the special
    # case of getset and member descriptors. In this case we
    # grab the module name from the class the descriptor was
    # being used in which is held in __objclass__.

    if hasattr(object, '__objclass__'):
        mname = getattr(object.__objclass__, '__module__', None)

    # The standard case is that we can just grab the __module__
    # attribute from the object.

    if mname is None:
        mname = getattr(object, '__module__', None)

    # An exception to that is builtins or any types which are
    # implemented in C code. For that we need to grab the module
    # name from the __class__. In doing this though, we need to
    # ensure we check for case of a bound method. In that case
    # we need to grab the module from the class of the instance
    # to which the method is bound.

    if mname is None:
        self = getattr(object, '__self__', None)
        if self is not None and hasattr(self, '__class__'):
            mname = getattr(self.__class__, '__module__', None)

    if mname is None and hasattr(object, '__class__'):
        mname = getattr(object.__class__, '__module__', None)

    # Finally, if the module name isn't in sys.modules, we will
    # format it within '<>' to denote that it is a generated
    # class of some sort where a fake namespace was used. This
    # happens for example with namedtuple classes in Python 3.

    if mname and mname not in sys.modules:
        mname = '<%s>' % mname

    # If unable to derive the module name, fallback to unknown.

    if not mname:
        mname = '<unknown>'

    return mname

def _object_context_py2(object):

    cname = None
    fname = None

    if inspect.isclass(object) or isinstance(object, type):
        # Old and new style class types.

        cname = object.__name__

    elif inspect.ismethod(object):
        # Bound and unbound class methods. In the case of an
        # unbound method the im_self attribute will be None. The
        # rules around whether im_self is an instance or a class
        # type are strange so need to cope with both.

        if object.im_self is not None:
            cname = getattr(object.im_self, '__name__', None)
            if cname is None:
                cname = getattr(object.im_self.__class__, '__name__')

        else:
            cname = object.im_class.__name__

        fname = object.__name__

    elif inspect.isfunction(object):
        # Normal functions and static methods. For a static we
        # method don't know of any way of being able to work out
        # the name of the class the static method is against.

        fname = object.__name__

    elif inspect.isbuiltin(object):
        # Builtin function. Can also be be bound to class to
        # create a method. Uses __self__ instead of im_self. The
        # rules around whether __self__ is an instance or a class
        # type are strange so need to cope with both.

        if object.__self__ is not None:
            cname = getattr(object.__self__, '__name__', None)
            if cname is None:
                cname = getattr(object.__self__.__class__, '__name__')

        fname = object.__name__

    elif isinstance(object, types.InstanceType):
        # Instances of old style classes. Instances of a class
        # don't normally have __name__. Where the object has a
        # __name__, assume it is likely going to be a decorator
        # implemented as a class and don't use the class name
        # else it mucks things up.

        fname = getattr(object, '__name__', None)

        if fname is None:
            cname = object.__class__.__name__

    elif hasattr(object, '__class__'):
        # Instances of new style classes. Instances of a class
        # don't normally have __name__. Where the object has a
        # __name__, assume it is likely going to be a decorator
        # implemented as a class and don't use the class name
        # else it mucks things up. The exception to this is when
        # it is a descriptor and has __objclass__, in which case
        # the class name from __objclass__ is used.

        fname = getattr(object, '__name__', None)

        if fname is not None:
            if hasattr(object, '__objclass__'):
                cname = object.__objclass__.__name__
            elif not hasattr(object, '__get__'):
                cname = object.__class__.__name__
        else:
            cname = object.__class__.__name__

    # Calculate the qualified path from the class name and the
    # function name.

    path = ''

    if cname:
        path = cname

    if fname:
        if path:
            path += '.'
        path += fname

    # Now calculate the name of the module object is defined in.

    owner = None

    if inspect.ismethod(object):
        if object.__self__ is not None:
            cname = getattr(object.__self__, '__name__', None)
            if cname is None:
                owner = object.__self__.__class__   # bound method
            else:
                owner = object.__self__             # class method

        else:
            owner = getattr(object, 'im_class', None)   # unbound method

    mname = _module_name(owner or object)

    return (mname, path)

def _object_context_py3(object):

    if inspect.ismethod(object):

        # In Python 3, ismethod() returns True for bound methods. We
        # need to distinguish between class methods and instance methods.
        #
        # First, test for class methods.

        cname = getattr(object.__self__, '__qualname__', None)

        # If it's not a class method, it must be an instance method.

        if cname is None:
            cname = getattr(object.__self__.__class__, '__qualname__')

        path = '%s.%s' % (cname, object.__name__)

    else:
        # For functions, the __qualname__ attribute gives us the name.
        # This will be a qualified name including the context in which
        # the function is defined in, such as an outer function in the
        # case of a nested function.

        path = getattr(object, '__qualname__', None)

        # If there is no __qualname__ it should mean it is a type
        # object of some sort. In this case we use the name from the
        # __class__. That also can be nested so need to use the
        # qualified name.

        if path is None and hasattr(object, '__class__'):
            path = getattr(object.__class__, '__qualname__')

    # Now calculate the name of the module object is defined in.

    owner = None

    if inspect.ismethod(object):
        if object.__self__ is not None:
            cname = getattr(object.__self__, '__name__', None)
            if cname is None:
                owner = object.__self__.__class__   # bound method
            else:
                owner = object.__self__             # class method

    mname = _module_name(owner or object)

    return (mname, path)

def object_context(target):
    """Returns a tuple identifying the supplied object. This will be of
    the form (module, object_path).

    """

    # Check whether the target is a functools.partial so we
    # can actually extract the contained function and use it.

    if isinstance(target, functools.partial):
        target = target.func

    # Check whether we have previously calculated the name
    # details for the target object and cached it against the
    # actual target object.

    details = getattr(target, '_nr_object_path', None)

    # Disallow cache lookup for python 3 methods. In the case where the method
    # is defined on a parent class, the name of the parent class is incorrectly
    # returned. Avoid this by recalculating the details each time.

    if details and not _is_py3_method(target):
        return details

    # Check whether the object is actually one of our own
    # wrapper classes. For these we use the convention that the
    # attribute _nr_last_object refers to the wrapped object
    # beneath the wrappers, there possibly being more than one
    # wrapper. We use the wrapped object when deriving the name
    # details and so bypass that chained calls that would need
    # to occur through the wrappers to get the attributes of the
    # original. For good measure, check that this wrapped object
    # didn't have the name details cached against it already.

    source = getattr(target, '_nr_last_object', None)

    if source:
        details = getattr(source, '_nr_object_path', None)

        if details and not _is_py3_method(source):
            return details

    else:
        source = target

    # If it wasn't cached we generate the name details and then
    # attempt to cache them against the object.

    if six.PY3:
        details = _object_context_py3(source)
    else:
        details = _object_context_py2(source)

    try:
        # If the original target is not the same as the source we
        # derive the name details from, then we are dealing with
        # a wrapper.

        if target is not source:

            # Although the original target could be a bound
            # wrapper still cache it against it anyway, in case
            # the bound wrapper is actually cached by the program
            # and used more than the one time.

            target._nr_object_path = details

        # Finally attempt to cache the name details against what
        # we derived them from. We may not be able to cache it if
        # it is a type implemented as C code or an object with
        # slots, which doesn't allow arbitrary addition of extra
        # attributes. In that case, if we actually have to rely
        # on the name details being cached against it and it fails,
        # we have no choice but to recalculate them every time.
        #
        # XXX We could consider for the case where it fails
        # storing it in a dictionary where the key is a weak
        # function proxy with a callback to remove the entry if
        # it ever expires. That would be another lookup we would
        # have to make and we are already doing a lot so would
        # have to properly benchmarks overhead before making that
        # choice.

        source._nr_object_path = details

    except Exception:
        pass

    return details

def callable_name(object, separator=':'):
    """Returns a string name identifying the supplied object. This will be
    of the form 'module:object_path'.

    If object were a function, then the name would be 'module:function. If
    a class, 'module:class'. If a member function, 'module:class.function'.

    By default the separator between the module path and the object path is
    ':' but can be overridden if necessary. The convention used by the
    Python Agent is that of using a ':' so it is clearer which part is the
    module name and which is the name of the object.

    """

    # The details are the module name and path. Join them with
    # the specified separator.

    return separator.join(object_context(object))

def expand_builtin_exception_name(name):

    # Convert name to module:name format, if it's a builtin Exception.
    # Otherwise, return it unchanged.

    try:
        exception = getattr(_exceptions_module, name)
    except AttributeError:
        pass
    else:
        if type(exception) is type and issubclass(exception, BaseException):
            return callable_name(exception)

    return name

def _is_py3_method(target):
    return six.PY3 and inspect.ismethod(target)

def parse_exc_info(exc_info):
    """Parse exc_info and return commonly used strings."""
    _, value, _ = exc_info

    module = value.__class__.__module__
    name = value.__class__.__name__

    if module:
        fullnames = ("%s:%s" % (module, name), "%s.%s" % (module, name))
    else:
        fullnames = (name,)

    try:

        # Favor unicode in exception messages.

        message = six.text_type(value)

    except Exception:
        try:

            # If exception cannot be represented in unicode, this means
            # that it is a byte string encoded with an encoding
            # that is not compatible with the default system encoding.
            # So, just pass this byte string along.

            message = str(value)

        except Exception:
            message = "<unprintable %s object>" % type(value).__name__

    return (module, name, fullnames, message)
