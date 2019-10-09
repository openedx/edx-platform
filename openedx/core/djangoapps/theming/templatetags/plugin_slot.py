from typing import Dict

from django.utils.safestring import mark_safe

from django.template import Library

from openedx.core.djangoapps.plugins.plugin_slots import get_content_for_slot

register = Library()


def plugin_slot(context: Dict[str], project_type: str, slot: str) -> str:
    """
    Get content to inject into templates from all registered plugins.
    """
    slot_namespace = getattr(context.get('request'), 'slot_namespace', None)
    if not slot_namespace:
        return ''
    content = get_content_for_slot(project_type, slot_namespace, slot, raw_context=context)
    return mark_safe(content)


register.simple_tag(plugin_slot, takes_context=True)
