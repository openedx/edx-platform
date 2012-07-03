from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml import XMLModuleStore


def import_from_xml(org, course, data_dir):
    """
    Import the specified xml data_dir into the django defined modulestore,
    using org and course as the location org and course.
    """
    module_store = XMLModuleStore(org, course, data_dir, 'xmodule.raw_module.RawDescriptor', eager=True)
    for module in module_store.modules.itervalues():
        modulestore().create_item(module.location)
        if 'data' in module.definition:
            modulestore().update_item(module.location, module.definition['data'])
        if 'children' in module.definition:
            modulestore().update_children(module.location, module.definition['children'])
        modulestore().update_metadata(module.location, dict(module.metadata))

    return module_store.course
