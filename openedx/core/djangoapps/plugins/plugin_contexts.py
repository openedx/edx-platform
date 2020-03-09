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
            try:
                module = import_module(module_path)
            except ImportError, ModuleNotFoundError:
                log.exception("Failed to import %s plugin when creating %s context", module_path, view_name)
                continue
            context_function = getattr(module, name, None)
            if context_function:
                plugin_context = context_function(existing_context)
            else:
                log.exception(
                    "Failed to call %s function from %s plugin when creating %s context",
                    name,
                    module_path,
                    view_name
                )
                continue

            # NOTE: If two plugins have try to set the same context keys, the last one
            # called will overwrite the others.
            for key in plugin_context:
                if key in aggregate_context:
                    log.warning(
                        "Plugin %s is overwriting the value of %s for view %s",
                        app_config.__module__,
                        key,
                        view_name
                    )
            aggregate_context.update(plugin_context)

    return aggregate_context


def _get_context_function(app_config, project_type, view_name):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    context_config = plugin_config.get(constants.PluginContexts.CONFIG, {})
    project_type_settings = context_config.get(project_type, {})
    return project_type_settings.get(view_name)
