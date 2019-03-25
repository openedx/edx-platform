from openedx.core.lib.plugins import PluginManager


class DjangoAppRegistry(PluginManager):
    """
    DjangoAppRegistry is a registry of django app plugins.
    """
    pass


def get_app_configs(project_type):
    return DjangoAppRegistry.get_available_plugins(project_type).itervalues()
