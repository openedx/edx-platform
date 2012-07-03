from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore
import logging

log = logging.getLogger(__name__)


def import_from_xml(org, course, data_dir):
    """
    Import the specified xml data_dir into the django defined modulestore,
    using org and course as the location org and course.
    """
    module_store = XMLModuleStore(org, course, data_dir, 'xmodule.raw_module.RawDescriptor', eager=True)
    for module in module_store.modules.itervalues():

        # TODO (cpennington): This forces import to overrite the same items.
        # This should in the future create new revisions of the items on import
        try:
            modulestore().create_item(module.location)
        except:
            log.exception('Item already exists at %s' % module.location.url())
            pass
        if 'data' in module.definition:
            modulestore().update_item(module.location, module.definition['data'])
        if 'children' in module.definition:
            modulestore().update_children(module.location, module.definition['children'])
        modulestore().update_metadata(module.location, dict(module.metadata))

    return module_store.course
