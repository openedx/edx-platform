"""A module proxy for delayed importing of modules.

From http://barnesc.blogspot.com/2006/06/automatic-python-imports-with-autoimp.html,
in the public domain.

"""

import sys


class LazyModule(object):
    """A lazy module proxy."""

    def __init__(self, modname):
        self.__dict__['__name__'] = modname
        self._set_mod(None)

    def _set_mod(self, mod):
        if mod is not None:
            self.__dict__ = mod.__dict__
        self.__dict__['_lazymod_mod'] = mod

    def _load_mod(self):
        __import__(self.__name__)
        self._set_mod(sys.modules[self.__name__])

    def __getattr__(self, name):
        if self.__dict__['_lazymod_mod'] is None:
            self._load_mod()

        mod = self.__dict__['_lazymod_mod']

        if hasattr(mod, name):
            return getattr(mod, name)
        else:
            try:
                subname = '%s.%s' % (self.__name__, name)
                __import__(subname)
                submod = getattr(mod, name)  # lint-amnesty, pylint: disable=unused-variable
            except ImportError:
                raise AttributeError("'module' object has no attribute %r" % name)  # lint-amnesty, pylint: disable=raise-missing-from
            self.__dict__[name] = LazyModule(subname)
            return self.__dict__[name]
