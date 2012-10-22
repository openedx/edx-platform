import logging
import os
import mimetypes

from .xml import XMLModuleStore
from .exceptions import DuplicateItemError
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent, XASSET_SRCREF_PREFIX

log = logging.getLogger(__name__)

def import_static_content(modules, data_dir, static_content_store):
    
    remap_dict = {}

    course_data_dir = None
    course_loc = None

    # quick scan to find the course module and pull out the data_dir and location
    # maybe there an easier way to look this up?!?

    for module in modules.itervalues():
        if module.category == 'course':
            course_loc = module.location
            course_data_dir = module.metadata['data_dir']

    if course_data_dir is None or course_loc is None:
        return remap_dict

   
    # now import all static assets
    static_dir = '{0}/static/'.format(course_data_dir)

    logging.debug("Importing static assets in {0}".format(static_dir))

    for dirname, dirnames, filenames in os.walk(static_dir):
        for filename in filenames:

            try:
                content_path = os.path.join(dirname, filename)
                fullname_with_subpath = content_path.replace(static_dir, '')  # strip away leading path from the name
                content_loc = StaticContent.compute_location(course_loc.org, course_loc.course, fullname_with_subpath)
                mime_type = mimetypes.guess_type(filename)[0]

                f = open(content_path, 'rb')
                data = f.read()
                f.close()

                content = StaticContent(content_loc, filename, mime_type, data)

                # first let's save a thumbnail so we can get back a thumbnail location
                thumbnail_content = static_content_store.generate_thumbnail(content)

                if thumbnail_content is not None:
                    content.thumbnail_location = thumbnail_content.location

                #then commit the content
                static_content_store.save(content)

                #store the remapping information which will be needed to subsitute in the module data
                remap_dict[fullname_with_subpath] = content_loc.name

            except:
                raise    

    return remap_dict

def import_from_xml(store, data_dir, course_dirs=None, 
                    default_class='xmodule.raw_module.RawDescriptor',
                    load_error_modules=True, static_content_store=None):
    """
    Import the specified xml data_dir into the "store" modulestore,
    using org and course as the location org and course.

    course_dirs: If specified, the list of course_dirs to load. Otherwise, load
    all course dirs

    """
    module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        course_dirs=course_dirs,
        load_error_modules=load_error_modules,
    )

    # NOTE: the XmlModuleStore does not implement get_items() which would be a preferable means
    # to enumerate the entire collection of course modules. It will be left as a TBD to implement that
    # method on XmlModuleStore.
    course_items = []
    for course_id in module_store.modules.keys():
        remap_dict = {}
        if static_content_store is not None:
            remap_dict = import_static_content(module_store.modules[course_id], data_dir, static_content_store)

        for module in module_store.modules[course_id].itervalues():

            if module.category == 'course':
                # HACK: for now we don't support progress tabs. There's a special metadata configuration setting for this.
                module.metadata['hide_progress_tab'] = True
                course_items.append(module)

            if 'data' in module.definition:
                module_data = module.definition['data']

                # cdodge: update any references to the static content paths
                # This is a bit brute force - simple search/replace - but it's unlikely that such references to '/static/....'
                # would occur naturally (in the wild)
                # @TODO, sorry a bit of technical debt here. There are some helper methods in xmodule_modifiers.py and static_replace.py which could
                # better do the url replace on the html rendering side rather than on the ingest side
                try:
                    if '/static/' in module_data:
                        for subkey in remap_dict.keys():
                            module_data = module_data.replace('/static/' + subkey, 'xasset:' + remap_dict[subkey])
                except:
                    pass    # part of the techincal debt is that module_data might not be a string (e.g. ABTest)

                store.update_item(module.location, module_data)


            if 'children' in module.definition:
                store.update_children(module.location, module.definition['children'])

            # NOTE: It's important to use own_metadata here to avoid writing
            # inherited metadata everywhere.
            store.update_metadata(module.location, dict(module.own_metadata))
            

    return module_store, course_items
