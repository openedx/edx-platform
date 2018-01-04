"""
Adds support for first class features that can be added to the edX platform.
"""

from stevedore.extension import ExtensionManager


class PluginError(Exception):
    """
    Base Exception for when an error was found regarding features.
    """
    pass


class PluginManager(object):
    """
    Base class that manages plugins to the edX platform.
    """
    @classmethod
    def get_available_plugins(cls):
        """
        Returns a dict of all the plugins that have been made available through the platform.
        """
        # Note: we're creating the extension manager lazily to ensure that the Python path
        # has been correctly set up. Trying to create this statically will fail, unfortunately.
        if not hasattr(cls, "_plugins"):
            plugins = {}
            extension_manager = ExtensionManager(namespace=cls.NAMESPACE)  # pylint: disable=no-member
            for plugin_name in extension_manager.names():
                plugins[plugin_name] = extension_manager[plugin_name].plugin
            cls._plugins = plugins
        return cls._plugins

    @classmethod
    def get_plugin(cls, name):
        """
        Returns the plugin with the given name.
        """
        plugins = cls.get_available_plugins()
        if name not in plugins:
            raise PluginError("No such plugin {name} for entry point {namespace}".format(
                name=name,
                namespace=cls.NAMESPACE  # pylint: disable=no-member
            ))
        return plugins[name]
