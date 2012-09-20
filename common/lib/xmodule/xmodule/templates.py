import logging
from fs.memoryfs import MemoryFS

from collections import defaultdict
from .x_module import XModuleDescriptor
from .mako_module import MakoDescriptorSystem
from .modulestore import Location
from .modulestore.django import modulestore

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
    def __init__(self):
        super(TemplateTestSystem, self).__init__(
            lambda *a, **k: None,
            MemoryFS(),
            lambda msg: None,
            render_template=lambda *a, **k: None,
        )


def update_templates():
    """
    Updates the set of templates in the modulestore with all templates currently
    available from the installed plugins
    """

    for category, templates in all_templates().items():
        for template in templates:
            if 'display_name' not in template.metadata:
                log.warning('No display_name specified in template {0}, skipping'.format(template))
                continue

            template_location = Location('i4x', 'edx', 'templates', category, Location.clean_for_url_name(template.metadata['display_name']))

            try:
                json_data = template._asdict()
                json_data['location'] = template_location.dict()
                XModuleDescriptor.load_from_json(json_data, TemplateTestSystem())
            except:
                log.warning('Unable to instantiate {cat} from template {template}, skipping'.format(
                    cat=category,
                    template=template
                ), exc_info=True)
                continue

            modulestore().update_item(template_location, template.data)
            modulestore().update_children(template_location, template.children)
            modulestore().update_metadata(template_location, template.metadata)
