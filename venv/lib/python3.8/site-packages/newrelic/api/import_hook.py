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

import logging
import sys

from newrelic.packages import six

_logger = logging.getLogger(__name__)

try:
    from importlib.util import find_spec
except ImportError:
    find_spec = None

_import_hooks = {}

_ok_modules = (
    # These modules are imported by the newrelic package and/or do not do
    # nested imports, so they're ok to import before newrelic.
    "urllib",
    "urllib2",
    "httplib",
    "http.client",
    "urllib.request",
    "newrelic.agent",
    "asyncio",
    "asyncio.events",
    # These modules should not be added to the _uninstrumented_modules set
    # because they have been deemed okay to import before initialization by
    # the customer.
    "gunicorn.app.base",
    "wsgiref.simple_server",
    "gevent.wsgi",
    "gevent.pywsgi",
    "cheroot.wsgi",
    "cherrypy.wsgiserver",
    "flup.server.cgi",
    "flup.server.ajp_base",
    "flup.server.fcgi_base",
    "flup.server.scgi_base",
    "meinheld.server",
    "paste.httpserver",
    "waitress.server",
    "gevent.monkey",
    "asyncio.base_events",
)

_uninstrumented_modules = set()


def register_import_hook(name, callable):  # pylint: disable=redefined-builtin
    if six.PY2:
        import imp

        imp.acquire_lock()

    try:
        hooks = _import_hooks.get(name, None)

        if name not in _import_hooks or hooks is None:

            # If no entry in registry or entry already flagged with
            # None then module may have been loaded, in which case
            # need to check and fire hook immediately.

            hooks = _import_hooks.get(name)

            module = sys.modules.get(name, None)

            if module is not None:

                # The module has already been loaded so fire hook
                # immediately.

                if module.__name__ not in _ok_modules:
                    _logger.debug(
                        "Module %s has been imported before the "
                        "newrelic.agent.initialize call. Import and "
                        "initialize the New Relic agent before all "
                        "other modules for best monitoring "
                        "results.",
                        module,
                    )

                    # Add the module name to the set of uninstrumented modules.
                    # During harvest, this set will be used to produce metrics.
                    # The adding of names here and the reading of them during
                    # harvest should be thread safe. This is because the code
                    # here is only run during `initialize` which will no-op if
                    # run multiple times (even if in a thread). The set is read
                    # from the harvest thread which will run one minute after
                    # `initialize` is called.

                    _uninstrumented_modules.add(module.__name__)

                _import_hooks[name] = None

                callable(module)

            else:

                # No hook has been registered so far so create list
                # and add current hook.

                _import_hooks[name] = [callable]

        else:

            # Hook has already been registered, so append current
            # hook.

            _import_hooks[name].append(callable)

    finally:
        if six.PY2:
            imp.release_lock()


def _notify_import_hooks(name, module):

    # Is assumed that this function is called with the global
    # import lock held. This should be the case as should only
    # be called from load_module() of the import hook loader.

    hooks = _import_hooks.get(name, None)

    if hooks is not None:
        _import_hooks[name] = None

        for hook in hooks:
            hook(module)


class _ImportHookLoader:
    def load_module(self, fullname):

        # Call the import hooks on the module being handled.

        module = sys.modules[fullname]
        _notify_import_hooks(fullname, module)

        return module


class _ImportHookChainedLoader:
    def __init__(self, loader):
        self.loader = loader

    def load_module(self, fullname):
        module = self.loader.load_module(fullname)

        # Call the import hooks on the module being handled.
        _notify_import_hooks(fullname, module)

        return module

    def create_module(self, spec):
        return self.loader.create_module(spec)

    def exec_module(self, module):
        self.loader.exec_module(module)

        # Call the import hooks on the module being handled.
        _notify_import_hooks(module.__name__, module)


class ImportHookFinder:
    def __init__(self):
        self._skip = {}

    def find_module(self, fullname, path=None):
        """
        Find spec and patch import hooks into loader before returning.

        Required for Python 2.

        https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.find_module
        """

        # If not something we are interested in we can return.

        if fullname not in _import_hooks:
            return None

        # Check whether this is being called on the second time
        # through and return.

        if fullname in self._skip:
            return None

        # We are now going to call back into import. We set a
        # flag to see we are handling the module so that check
        # above drops out on subsequent pass and we don't go
        # into an infinite loop.

        self._skip[fullname] = True

        try:
            # For Python 3 we need to use find_spec() from the importlib
            # module.

            if find_spec:
                spec = find_spec(fullname)
                loader = getattr(spec, "loader", None)

                if loader and not isinstance(loader, (_ImportHookChainedLoader, _ImportHookLoader)):
                    return _ImportHookChainedLoader(loader)

            else:
                __import__(fullname)

                # If we get this far then the module we are
                # interested in does actually exist and so return
                # our loader to trigger import hooks and then return
                # the module.

                return _ImportHookLoader()

        finally:
            del self._skip[fullname]

    def find_spec(self, fullname, path=None, target=None):
        """
        Find spec and patch import hooks into loader before returning.

        Required for Python 3.10+ to avoid warnings.

        https://docs.python.org/3/library/importlib.html#importlib.abc.MetaPathFinder.find_spec
        """

        # If not something we are interested in we can return.

        if fullname not in _import_hooks:
            return None

        # Check whether this is being called on the second time
        # through and return.

        if fullname in self._skip:
            return None

        # We are now going to call back into import. We set a
        # flag to see we are handling the module so that check
        # above drops out on subsequent pass and we don't go
        # into an infinite loop.

        self._skip[fullname] = True

        try:
            # For Python 3 we need to use find_spec() from the importlib
            # module.

            if find_spec:
                spec = find_spec(fullname)
                loader = getattr(spec, "loader", None)

                if loader and not isinstance(loader, (_ImportHookChainedLoader, _ImportHookLoader)):
                    spec.loader = _ImportHookChainedLoader(loader)

                return spec

            else:
                # Not possible, Python 3 defines find_spec and Python 2 does not have find_spec on Finders
                return None

        finally:
            del self._skip[fullname]


def import_hook(name):
    def decorator(wrapped):
        register_import_hook(name, wrapped)
        return wrapped

    return decorator


def import_module(name):
    __import__(name)
    return sys.modules[name]
