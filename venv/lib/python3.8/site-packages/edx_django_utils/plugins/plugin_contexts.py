"""
Various functions to get view contexts

Please remember to expose any new public methods in the `__init__.py` file.
"""
import functools
from importlib import import_module
from logging import getLogger

from . import constants, registry

log = getLogger(__name__)


def get_plugins_view_context(project_type, view_name, existing_context=None):
    """
    Returns a dict of additional view context. Will check if any plugin apps
    have that view in their view_context_config, and if so will call their
    selected function to get their context dicts.

    Params:
        project_type: a string that determines which project (lms or studio) the view is being called in. See the
            ProjectType enum in plugins/constants.py for valid options
        view_name: a string that determines which view needs the additional context. These are globally unique and
            noted in the api.py in the view's app.
        existing_context: a dictionary which includes all of the data that the page was going to render with prior
            to the addition of each plugin's context. This is what will be passed to plugins so they may choose
            what data to add to the view.
    """
    aggregate_context = {"plugins": {}}

    if existing_context is None:
        existing_context = {}

    context_functions = _get_cached_context_functions_for_view(project_type, view_name)

    for (context_function, plugin_name) in context_functions:
        try:
            plugin_context = context_function(existing_context)
        except Exception as exc:  # pylint: disable=broad-except
            # We're catching this because we don't want the core to blow up when a
            # plugin is broken. This exception will probably need some sort of
            # monitoring hooked up to it to make sure that these errors don't go
            # unseen.
            log.exception("Failed to call plugin context function. Error: %s", exc)
            continue

        aggregate_context["plugins"][plugin_name] = plugin_context

    return aggregate_context


@functools.lru_cache(maxsize=None)
def _get_cached_context_functions_for_view(project_type, view_name):
    """
    Returns a list of tuples where the first item is the context function
    and the second item is the name of the plugin it's being called from.

    NOTE: These will be functions will be cached (in RAM not memcache) on this unique
    combination. If we enable many new views to use this system, we may notice an
    increase in memory usage as the entirety of these functions will be held in memory.
    """
    context_functions = []
    for app_config in registry.get_plugin_app_configs(project_type):
        context_function_path = _get_context_function_path(
            app_config, project_type, view_name
        )
        if context_function_path:
            module_path, _, name = context_function_path.rpartition(".")
            try:
                module = import_module(module_path)
            except ImportError:
                log.exception(
                    "Failed to import %s plugin when creating %s context",
                    module_path,
                    view_name,
                )
                continue
            context_function = getattr(module, name, None)
            if context_function:
                plugin_name, _, _ = module_path.partition(".")
                context_functions.append((context_function, plugin_name))
            else:
                log.warning(
                    "Failed to retrieve %s function from %s plugin when creating %s context",
                    name,
                    module_path,
                    view_name,
                )
    return context_functions


def _get_context_function_path(app_config, project_type, view_name):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    context_config = plugin_config.get(constants.PluginContexts.CONFIG, {})
    project_type_settings = context_config.get(project_type, {})
    return project_type_settings.get(view_name)
