"""
Urls utility functions

Please remember to expose any new public methods in the `__init__.py` file.
"""
from logging import getLogger

from django.urls import include, re_path

from . import constants, registry, utils

log = getLogger(__name__)


def _get_url(url_module_path, url_config):
    """
    function constructs the appropriate URL
    """
    namespace = url_config[constants.PluginURLs.NAMESPACE]
    app_name = url_config.get(constants.PluginURLs.APP_NAME)
    regex = url_config.get(constants.PluginURLs.REGEX, r"")

    if namespace:
        return re_path(regex, include((url_module_path, app_name), namespace=namespace))
    else:
        return re_path(regex, include(url_module_path))


def get_plugin_url_patterns(project_type):
    """
    Returns a list of all registered Plugin URLs, expected to be added to
    the URL patterns for the given project_type.
    """
    return [
        _get_url(url_module_path, url_config)
        for url_module_path, url_config in _iter_plugins(project_type)
    ]


def _iter_plugins(project_type):
    """
    Yields the module path and configuration for Plugin URLs registered for
    the given project_type.
    """
    for app_config in registry.get_plugin_app_configs(project_type):
        url_config = _get_config(app_config, project_type)
        if url_config is None:
            log.debug(
                "Plugin Apps [URLs]: Did NOT find %s for %s",
                app_config.name,
                project_type,
            )
            continue

        urls_module_path = utils.get_module_path(
            app_config, url_config, constants.PluginURLs
        )
        url_config[constants.PluginURLs.NAMESPACE] = url_config.get(
            constants.PluginURLs.NAMESPACE, app_config.name
        )
        url_config[constants.PluginURLs.APP_NAME] = app_config.name
        log.debug(
            "Plugin Apps [URLs]: Found %s with namespace %s for %s",
            app_config.name,
            url_config[constants.PluginURLs.NAMESPACE],
            project_type,
        )
        yield urls_module_path, url_config


def _get_config(app_config, project_type):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    url_config = plugin_config.get(constants.PluginURLs.CONFIG, {})
    return url_config.get(project_type)
