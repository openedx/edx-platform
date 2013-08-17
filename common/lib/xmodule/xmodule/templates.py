"""
This module handles loading xmodule templates from disk into the modulestore.
These templates are used by the CMS to provide baseline content that
can be cloned when adding new modules to a course.

`Template`s are defined in x_module. They contain 3 attributes:
    metadata: A dictionary with the template metadata. This should contain
        any values for fields
            * with scope Scope.settings
            * that have values different than the field defaults
            * and that are to be editable in Studio
    data: A JSON value that defines the template content. This should be a dictionary
        containing values for fields
            * with scope Scope.content
            * that have values different than the field defaults
            * and that are to be editable in Studio
        or, if the module uses a single Scope.content String field named `data`, this
        should be a string containing the contents of that field
    children: A list of Location urls that define the template children

Templates are defined on XModuleDescriptor types, in the template attribute.
"""


import logging
from fs.memoryfs import MemoryFS

from collections import defaultdict
from .x_module import XModuleDescriptor
from .mako_module import MakoDescriptorSystem
from .modulestore import Location

log = logging.getLogger(__name__)


def all_templates():
    """
    Returns all templates for enabled modules, grouped by descriptor type
    """

    templates = defaultdict(list)
    for category, descriptor in XModuleDescriptor.load_classes():
        templates[category] = descriptor.templates()

    return templates


class TemplateTestSystem(MakoDescriptorSystem):
    """
    This system exists to help verify that XModuleDescriptors can be instantiated
    from their defined templates before we load the templates into the modulestore.
    """
    def __init__(self):
        super(TemplateTestSystem, self).__init__(
            lambda *a, **k: None,
            MemoryFS(),
            lambda msg: None,
            render_template=lambda *a, **k: None,
        )


def update_templates(modulestore):
    """
    Updates the set of templates in the modulestore with all templates currently
    available from the installed plugins
    """

    # cdodge: build up a list of all existing templates. This will be used to determine which
    # templates have been removed from disk - and thus we need to remove from the DB
    templates_to_delete = modulestore.get_items(['i4x', 'edx', 'templates', None, None, None])

    for category, templates in all_templates().items():
        for template in templates:
            if 'display_name' not in template.metadata:
                log.warning('No display_name specified in template {0}, skipping'.format(template))
                continue

            template_location = Location('i4x', 'edx', 'templates', category, Location.clean_for_url_name(template.metadata['display_name']))

            try:
                json_data = {
                    'definition': {
                        'data': template.data,
                        'children': template.children
                    },
                    'metadata': template.metadata
                }
                json_data['location'] = template_location.dict()

                XModuleDescriptor.load_from_json(json_data, TemplateTestSystem())
            except:
                log.warning('Unable to instantiate {cat} from template {template}, skipping'.format(
                    cat=category,
                    template=template
                ), exc_info=True)
                continue

            modulestore.update_item(template_location, template.data)
            modulestore.update_children(template_location, template.children)
            modulestore.update_metadata(template_location, template.metadata)

            # remove template from list of templates to delete
            templates_to_delete = [t for t in templates_to_delete if t.location != template_location]

    # now remove all templates which appear to have removed from disk
    if len(templates_to_delete) > 0:
        logging.debug('deleting dangling templates = {0}'.format(templates_to_delete))
        for template in templates_to_delete:
            modulestore.delete_item(template.location)
