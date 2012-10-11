import logging
import os
import mimetypes

from .xml import XMLModuleStore
from .exceptions import DuplicateItemError
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent

log = logging.getLogger(__name__)


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

    for course_id in module_store.modules.keys():
        course_data_dir = None
        course_loc = None

        for module in module_store.modules[course_id].itervalues():

            if module.category == 'course':
                course_loc = module.location

            if 'data' in module.definition:
                store.update_item(module.location, module.definition['data'])
            if 'children' in module.definition:
                store.update_children(module.location, module.definition['children'])
            # NOTE: It's important to use own_metadata here to avoid writing
            # inherited metadata everywhere.
            store.update_metadata(module.location, dict(module.own_metadata))
            course_data_dir = module.metadata['data_dir']

        if static_content_store is not None:
            ''' 
            now import all static assets
            '''
            static_dir = '{0}/{1}/static/'.format(data_dir, course_data_dir)

            for dirname, dirnames, filenames in os.walk(static_dir):
                for filename in filenames:

                    try:
                        content_path = os.path.join(dirname, filename)
                        fullname_with_subpath = content_path.replace(static_dir, '')  # strip away leading path from the name
                        content_loc = StaticContent.compute_location(course_loc.org, course_loc.course, fullname_with_subpath)
                        mime_type = mimetypes.guess_type(filename)[0]

                        print 'importing static asset {0} of mime-type {1} from path {2}'.format(content_loc, 
                            mime_type, content_path)

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
                    except:
                        raise

    return module_store
