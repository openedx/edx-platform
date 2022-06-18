"""
Methods to get plugin apps

Please remember to expose any new public methods in the `__init__.py` file.
"""
from logging import getLogger

from . import constants, registry

log = getLogger(__name__)


def get_plugin_apps(project_type):
    """
    Returns a list of all registered Plugin Apps, expected to be added to
    the INSTALLED_APPS list for the given project_type.
    """
    plugin_apps = [
        "{module_name}.{class_name}".format(
            module_name=app_config.__module__, class_name=app_config.__name__,
        )
        for app_config in registry.get_plugin_app_configs(project_type)
        if getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, None)
        is not None
    ]
    log.debug("Plugin Apps: Found %s", plugin_apps)
    return plugin_apps
