"""
Functions that deal with settings related to plugins

Please remember to expose any new public methods in the `__init__.py` file.
"""
from logging import getLogger

from . import constants, registry, utils

log = getLogger(__name__)


def add_plugins(settings_path, project_type, settings_type):
    """
    Updates the module at the given ``settings_path`` with all Plugin
    Settings appropriate for the given project_type and settings_type.
    """
    settings_module = utils.import_module(settings_path)
    for plugin_settings in _iter_plugins(project_type, settings_type):
        settings_func = getattr(
            plugin_settings, constants.PLUGIN_APP_SETTINGS_FUNC_NAME
        )
        settings_func(settings_module)


def _iter_plugins(project_type, settings_type):
    """
    Yields Plugin Settings modules that are registered for the given
    project_type and settings_type.
    """
    for app_config in registry.get_plugin_app_configs(project_type):
        settings_config = _get_config(app_config, project_type, settings_type)
        if settings_config is None:
            log.debug(
                "Plugin Apps [Settings]: Did NOT find %s for %s and %s",
                app_config.name,
                project_type,
                settings_type,
            )
            continue

        plugin_settings_path = utils.get_module_path(
            app_config, settings_config, constants.PluginSettings
        )

        log.debug(
            "Plugin Apps [Settings]: Found %s for %s and %s",
            app_config.name,
            project_type,
            settings_type,
        )
        yield utils.import_module(plugin_settings_path)


def _get_config(app_config, project_type, settings_type):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    settings_config = plugin_config.get(constants.PluginSettings.CONFIG, {})
    project_type_settings = settings_config.get(project_type, {})
    return project_type_settings.get(settings_type)
