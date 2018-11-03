"""
This is a set of reference implementations for XBlock plugins
(XBlocks, Fields, and Services).

The README file in this directory contains much more information.

Much of this still needs to be organized.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

try:
    from django.core.exceptions import ImproperlyConfigured
except ImportError:
    class ImproperlyConfigured(Exception):
        '''
        If Django is installed, and djpyfs is installed, but we're not in a
        Django app, we'll get this exception. We'd like to catch
        it. But we don't want the try/except to fail even if we're
        either in a proper Django app, or don't have Django installed
        at all.
        '''
        pass

try:
    from djpyfs import djpyfs  # pylint: disable=import-error
except ImportError:
    djpyfs = None  # pylint: disable=invalid-name
except ImproperlyConfigured:
    print("Warning! Django is not correctly configured.")
    djpyfs = None  # pylint: disable=invalid-name

from xblock.fields import Field, NO_CACHE_VALUE
from xblock.fields import scope_key

#  Finished services


def public(type=None, **kwargs):  # pylint: disable=unused-argument, redefined-builtin
    """
    Mark a function as public. In the future, this will inform the
    XBlocks services framework to make the function remotable. For
    now, this is a placeholder.

    The kwargs will contain:

      type : A specification for what the function does. Multiple
      functions of the same type will have identical input/output
      semantics, but may have different implementations. For example,

        type = student_distance

      Takes two students and returns a number. Specific instances may
      look at e.g. difference in some measure of aptitude, geographic
      distance, culture, or language. See stevedor, as well as queries
      in https://github.com/edx/insights to understand how this will
      be used.
    """

    def wrapper(function):
        """
        Just return the function (for now)
        """
        return function

    return wrapper


class Service(object):
    """
    Top-level definition for an XBlocks service.

    This is intended as a starting point for discussion, not
    necessarily a finished interface.

    Possible goals:
    * Right now, they derive from object. We'd like there to be a
      common superclass.
    * We'd like to be able to provide both language-level and
      service-level bindings.
    * We'd like them to have a basic knowledge of context (what block
      they're being called from, access to the runtime, dependencies,
      etc.
    * That said, we'd like to not over-initialize. Services may have
      expensive initializations, and a per-block initialization may be
      prohibitive.
    * We'd like them to be able to load through Stevedor, and have a
      plug-in mechanism similar to XBlock.
    """
    def __init__(self, **kwargs):
        # TODO: We need plumbing to set these
        self._runtime = kwargs.get('runtime', None)
        self._xblock = kwargs.get('xblock', None)
        self._user = kwargs.get('user', None)

    def xblock(self):
        """
        Accessor for the xblock calling the service. Returns None if unknown
        """
        return self._xblock

    def runtime(self):
        """
        Accessor for the runtime object. Returns None if unknown
        """
        return self._runtime


class Filesystem(Field):
    """An enhanced pyfilesystem.

    This returns a file system provided by the runtime. The file
    system has two additional methods over a normal pyfilesytem:

    * `get_url` allows it to return a URL for a file
    * `expire` allows it to create files which may be garbage
      collected after a preset period. `edx-platform` and
      `xblock-sdk` do not currently garbage collect them,
      however.

    More information can be found at: http://docs.pyfilesystem.org/en/latest/
    and https://github.com/pmitros/django-pyfs

    The major use cases for this are storage of large binary objects,
    pregenerating per-student data (e.g. `pylab` plots), and storing
    data which should be downloadable (for example, serving <img
    src=...> will typically be faster through this than serving that
    up through XBlocks views.
    """
    MUTABLE = False

    def __get__(self, xblock, xblock_class):
        """
        Returns a `pyfilesystem` object which may be interacted with.
        """
        # Prioritizes the cached value over obtaining the value from
        # the field-data service. Thus if a cached value exists, that
        # is the value that will be returned. Otherwise, it will get
        # it from the fs service.

        # pylint: disable=protected-access
        if xblock is None:
            return self

        value = self._get_cached_value(xblock)
        if value is NO_CACHE_VALUE:
            value = xblock.runtime.service(xblock, 'fs').load(self, xblock)
            self._set_cached_value(xblock, value)

        return value

    def __delete__(self, xblock):
        """
        We don't support this until we figure out what this means. Files
        should be deleted through normal pyfilesystem operations.
        """
        raise NotImplementedError

    def __set__(self, xblock, value):
        """
        We interact with a file system by `open`/`close`/`read`/`write`,
        not `set` and `get`.

        We don't support this until we figure out what this means. In
        the future, this might be used to e.g. store some kind of
        metadata about the file system in the KVS (perhaps prefix and
        location or similar?)
        """
        raise NotImplementedError

#  edX-internal prototype services


class FSService(Service):
    """
    This is a PROTOTYPE service for storing files in XBlock fields.

    It returns a file system as per:
    https://github.com/pmitros/django-pyfs

    1) We want to change how load() works, and specifically how
    prefixes are calculated.
    2) There is discussion as to whether we want this service at
    all. Specifically:
    - It is unclear if XBlocks ought to have filesystem-as-a-service,
      or just as a field, as per below. Below requires an FS service,
      but it is not clear XBlocks should know about it.
    """
    @public()
    def load(self, instance, xblock):
        """
        Get the filesystem for the field specified in 'instance' and the
        xblock in 'xblock' It is locally scoped.
        """

        # TODO: Get xblock from context, once the plumbing is piped through
        if djpyfs:
            return djpyfs.get_filesystem(scope_key(instance, xblock))
        else:
            # The reference implementation relies on djpyfs
            # https://github.com/edx/django-pyfs
            # For Django runtimes, you may use this reference
            # implementation. Otherwise, you will need to
            # patch pyfilesystem yourself to implement get_url.
            raise NotImplementedError("djpyfs not available")

    def __repr__(self):
        return "File system object"
