from importlib import import_module

from logging import getLogger

from openedx.core.lib.cache_utils import process_cached

from . import constants, registry
from .utils import get_cached_functions_for_plugin


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

    context_functions = get_cached_functions_for_plugin(_get_context_function_path, project_type, view_name)

    for (context_function, plugin_name) in context_functions:
        try:
            plugin_context = context_function(existing_context)
        except Exception as exc:
            # We're catching this because we don't want the core to blow up when a
            # plugin is broken. This exception will probably need some sort of
            # monitoring hooked up to it to make sure that these errors don't go
            # unseen.
            log.exception("Failed to call plugin context function. Error: %s", exc)
            continue

        aggregate_context["plugins"][plugin_name] = plugin_context

    return aggregate_context


def _get_context_function_path(app_config, project_type, view_name):
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    context_config = plugin_config.get(constants.PluginContexts.CONFIG, {})
    project_type_settings = context_config.get(project_type, {})
    return project_type_settings.get(view_name)
