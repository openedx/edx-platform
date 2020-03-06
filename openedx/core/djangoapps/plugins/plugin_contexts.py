from importlib import import_module

from logging import getLogger
from . import constants, registry

log = getLogger(__name__)


def get_plugins_view_context(project_type, view_name, existing_context={}):
    """
    Returns a dict of additonal view context. Will check if any plugin apps
    have that view in their context_config, and if so will call their
    selected function to get their context dicts.
    """
    aggregate_context = {}

    for app_config in registry.get_app_configs(project_type):
        context_function_path = _get_context_function(app_config, project_type, view_name)
        if context_function_path:
            module_path, _, name = context_function_path.rpartition('.')
            context_function = getattr(import_module(module_path), name)
            plugin_context = context_function(existing_context)

            # NOTE: If two plugins have try to set the same context keys, the last one
            # called will overwrite the others.
            aggregate_context.update(plugin_context)

    return aggregate_context


def _get_context_function(app_config, project_type, view_name):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    context_config = plugin_config.get(constants.PluginContexts.CONFIG, {})
    project_type_settings = context_config.get(project_type, {})
    return project_type_settings.get(view_name)
