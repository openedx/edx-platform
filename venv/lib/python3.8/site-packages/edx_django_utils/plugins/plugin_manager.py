"""
Adds support for first class plugins that can be added to an IDA.

Please remember to expose any new public methods in the `__init__.py` file.
"""

import functools
from collections import OrderedDict

from stevedore.extension import ExtensionManager


class PluginError(Exception):
    """
    Base Exception for when an error was found regarding plugins.
    """


class PluginManager:
    """
    Base class that manages plugins for an IDA.
    """

    @classmethod
    @functools.lru_cache(maxsize=None)
    def get_available_plugins(cls, namespace=None):
        """
        Returns a dict of all the plugins that have been made available.
        """
        # Note: we're creating the extension manager lazily to ensure that the Python path
        # has been correctly set up. Trying to create this statically will fail, unfortunately.
        plugins = OrderedDict()
        # pylint: disable=no-member
        extension_manager = ExtensionManager(
            namespace=namespace or cls.NAMESPACE
        )
        for plugin_name in extension_manager.names():
            plugins[plugin_name] = extension_manager[plugin_name].plugin
        return plugins

    @classmethod
    def get_plugin(cls, name, namespace=None):
        """
        Returns the plugin with the given name.
        """
        plugins = cls.get_available_plugins(namespace)
        if name not in plugins:
            raise PluginError(
                "No such plugin {name} for entry point {namespace}".format(
                    name=name,
                    namespace=namespace or cls.NAMESPACE,  # pylint: disable=no-member
                )
            )
        return plugins[name]
