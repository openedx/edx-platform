from logging import getLogger
from typing import Dict

from django.apps import AppConfig

from . import constants
from .plugin_contexts import get_plugins_view_context
from .utils import get_cached_functions_for_plugin

log = getLogger(__name__)

COMMON_ALLOW_LIST = ['request', 'current_url']


def get_content_for_slot(project_type: str, slot_namespace: str, slot_name: str, raw_context: Dict) -> str:
    """
    Returns a list of additional content for a view slot. Will check if any plugin apps
    have that view in their slots_configs, and if so will call their selected function to
    get injected content for the slot.

    Args:
        project_type (str): a string that determines which project (lms or studio) the view is being called in. See the
            ProjectType enum in plugins/constants.py for valid options
        slot_namespace (str): a string that specifies the namespace for this slot.
        slot_name (str): a string that determines which slot the plugin will render content for. These are unique for
            each project type.
        raw_context (Dict): the unfiltered context available to the internal view.
    """
    aggregate_slot_content = u""
    slot_functions = get_cached_functions_for_plugin(_get_slots_function_path, project_type, slot_namespace, slot_name)

    # Each view can pass the approved part of the context, in the context itself.
    context_allow_list = raw_context.get('context_allow_list', [])
    if context_allow_list == '*':
        allowed_context = raw_context
    else:
        # The request object is allowed by default, and always available.
        context_allow_list.extend(COMMON_ALLOW_LIST)

        allowed_context = {
            key: raw_context.get(key)
            for key in context_allow_list
        }

    for (slot_function, plugin_name) in slot_functions:
        try:
            # Allow plugins to extend the context for other plugins
            context = get_plugins_view_context(
                constants.ProjectType.LMS,
                plugin_name,
                raw_context,
            )
            context.update(allowed_context)
            plugin_slot_content = slot_function(context)
            aggregate_slot_content += plugin_slot_content

        except Exception as exc:
            # We're catching this because we don't want the core to blow up when a
            # plugin is broken. This exception will probably need some sort of
            # monitoring hooked up to it to make sure that these errors don't go
            # unseen.
            log.exception("Failed to call plugin slot function. Error: %s", exc)
            continue

    return aggregate_slot_content


def _get_slots_function_path(app_config: AppConfig, project_type: str, slot_namespace: str, slot_name: str) -> str:
    plugin_config = getattr(app_config, constants.PLUGIN_APP_CLASS_ATTRIBUTE_NAME, {})
    slots_config = plugin_config.get(constants.PluginSlots.CONFIG, {})
    project_type_settings = slots_config.get(project_type, {})
    slot_namespace_settings = project_type_settings.get(slot_namespace, {})
    return slot_namespace_settings.get(slot_name)
