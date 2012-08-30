import logging

from .xml import XMLModuleStore
from .exceptions import DuplicateItemError

log = logging.getLogger(__name__)


def import_from_xml(store, data_dir, course_dirs=None, 
                    default_class='xmodule.raw_module.RawDescriptor'):
    """
    Import the specified xml data_dir into the "store" modulestore,
    using org and course as the location org and course.

    course_dirs: If specified, the list of course_dirs to load. Otherwise, load
    all course dirs

    """
    module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        course_dirs=course_dirs
    )
    for course_id in module_store.modules.keys():
        for module in module_store.modules[course_id].itervalues():

            # TODO (cpennington): This forces import to overrite the same items.
            # This should in the future create new revisions of the items on import
            try:
                store.create_item(module.location)
            except DuplicateItemError:
                log.exception('Item already exists at %s' % module.location.url())
                pass
            if 'data' in module.definition:
                store.update_item(module.location, module.definition['data'])
            if 'children' in module.definition:
                store.update_children(module.location, module.definition['children'])
            # NOTE: It's important to use own_metadata here to avoid writing
            # inherited metadata everywhere.
            store.update_metadata(module.location, dict(module.own_metadata))

    return module_store
