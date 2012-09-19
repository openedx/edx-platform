from collections import defaultdict
from .x_module import XModuleDescriptor
from .modulestore import Location
from .modulestore.django import modulestore


def all_templates():
    """
    Returns all templates for enabled modules, grouped by descriptor type
    """

    templates = defaultdict(list)
    for category, descriptor in XModuleDescriptor.load_classes():
        templates[category] = descriptor.templates

    return templates


def update_templates():
    """
    Updates the set of templates in the modulestore with all templates currently
    available from the installed plugins
    """

    for category, templates in all_templates().items():
        for template in templates:
            template_location = Location('i4x', 'edx', 'templates', category, Location.clean_for_url_name(template.name))
            modulestore().update_item(template_location, template.data)
            modulestore().update_children(template_location, template.children)
            modulestore().update_metadata(template_location, {'display_name': template.name})
