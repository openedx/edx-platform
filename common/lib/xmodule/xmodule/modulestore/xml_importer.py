import logging
import os
import mimetypes
from lxml.html import rewrite_links as lxml_rewrite_links
from path import path

from xblock.core import Scope

from .xml import XMLModuleStore, ImportSystem, ParentTracker
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from .inheritance import own_metadata
from xmodule.errortracker import make_error_tracker

log = logging.getLogger(__name__)


def import_static_content(modules, course_loc, course_data_path, static_content_store, target_location_namespace,
                          subpath='static', verbose=False):

    remap_dict = {}

    # now import all static assets
    static_dir = course_data_path / subpath

    verbose = True

    for dirname, dirnames, filenames in os.walk(static_dir):
        for filename in filenames:

            try:
                content_path = os.path.join(dirname, filename)
                if verbose:
                    log.debug('importing static content {0}...'.format(content_path))

                fullname_with_subpath = content_path.replace(static_dir, '')  # strip away leading path from the name
                if fullname_with_subpath.startswith('/'):
                    fullname_with_subpath = fullname_with_subpath[1:]
                content_loc = StaticContent.compute_location(target_location_namespace.org, target_location_namespace.course, fullname_with_subpath)
                mime_type = mimetypes.guess_type(filename)[0]

                with open(content_path, 'rb') as f:
                    data = f.read()

                content = StaticContent(content_loc, filename, mime_type, data, import_path=fullname_with_subpath)

                # first let's save a thumbnail so we can get back a thumbnail location
                (thumbnail_content, thumbnail_location) = static_content_store.generate_thumbnail(content)

                if thumbnail_content is not None:
                    content.thumbnail_location = thumbnail_location

                #then commit the content
                static_content_store.save(content)

                #store the remapping information which will be needed to subsitute in the module data
                remap_dict[fullname_with_subpath] = content_loc.name
            except:
                raise

    return remap_dict


def verify_content_links(module, base_dir, static_content_store, link, remap_dict=None):
    if link.startswith('/static/'):
        # yes, then parse out the name
        path = link[len('/static/'):]

        static_pathname = base_dir / path

        if os.path.exists(static_pathname):
            try:
                content_loc = StaticContent.compute_location(module.location.org, module.location.course, path)
                filename = os.path.basename(path)
                mime_type = mimetypes.guess_type(filename)[0]

                with open(static_pathname, 'rb') as f:
                    data = f.read()

                content = StaticContent(content_loc, filename, mime_type, data, import_path=path)

                # first let's save a thumbnail so we can get back a thumbnail location
                (thumbnail_content, thumbnail_location) = static_content_store.generate_thumbnail(content)

                if thumbnail_content is not None:
                    content.thumbnail_location = thumbnail_location

                #then commit the content
                static_content_store.save(content)

                new_link = StaticContent.get_url_path_from_location(content_loc)

                if remap_dict is not None:
                    remap_dict[link] = new_link

                return new_link
            except Exception, e:
                logging.exception('Skipping failed content load from {0}. Exception: {1}'.format(path, e))

    return link


def import_module_from_xml(modulestore, static_content_store, course_data_path, module, target_location_namespace=None, verbose=False):
    # remap module to the new namespace
    if target_location_namespace is not None:
        # This looks a bit wonky as we need to also change the 'name' of the imported course to be what
        # the caller passed in
        if module.location.category != 'course':
            module.location = module.location._replace(tag=target_location_namespace.tag, org=target_location_namespace.org,
                                                       course=target_location_namespace.course)
        else:
            module.location = module.location._replace(tag=target_location_namespace.tag, org=target_location_namespace.org,
                                                       course=target_location_namespace.course, name=target_location_namespace.name)

        # then remap children pointers since they too will be re-namespaced
        if module.has_children:
            children_locs = module.children
            new_locs = []
            for child in children_locs:
                child_loc = Location(child)
                new_child_loc = child_loc._replace(tag=target_location_namespace.tag, org=target_location_namespace.org,
                                                   course=target_location_namespace.course)

                new_locs.append(new_child_loc.url())

            module.children = new_locs

    if hasattr(module, 'data'):
        # cdodge: now go through any link references to '/static/' and make sure we've imported
        # it as a StaticContent asset
        try:
            remap_dict = {}

            # use the rewrite_links as a utility means to enumerate through all links
            # in the module data. We use that to load that reference into our asset store
            # IMPORTANT: There appears to be a bug in lxml.rewrite_link which makes us not be able to
            # do the rewrites natively in that code.
            # For example, what I'm seeing is <img src='foo.jpg' />   ->   <img src='bar.jpg'>
            # Note the dropped element closing tag. This causes the LMS to fail when rendering modules - that's
            # no good, so we have to do this kludge
            if isinstance(module.data, str) or isinstance(module.data, unicode):  # some module 'data' fields are non strings which blows up the link traversal code
                lxml_rewrite_links(module.data, lambda link: verify_content_links(module, course_data_path, static_content_store, link, remap_dict))

                for key in remap_dict.keys():
                    module.data = module.data.replace(key, remap_dict[key])

        except Exception:
            logging.exception("failed to rewrite links on {0}. Continuing...".format(module.location))

        modulestore.update_item(module.location, module.data)

    if module.has_children:
        modulestore.update_children(module.location, module.children)

    modulestore.update_metadata(module.location, own_metadata(module))


def import_course_from_xml(modulestore, static_content_store, course_data_path, module, target_location_namespace=None, verbose=False):
    # cdodge: more hacks (what else). Seems like we have a problem when importing a course (like 6.002) which
    # does not have any tabs defined in the policy file. The import goes fine and then displays fine in LMS,
    # but if someone tries to add a new tab in the CMS, then the LMS barfs because it expects that -
    # if there is *any* tabs - then there at least needs to be some predefined ones
    if module.tabs is None or len(module.tabs) == 0:
        module.tabs = [{"type": "courseware"},
                       {"type": "course_info", "name": "Course Info"},
                       {"type": "discussion", "name": "Discussion"},
                       {"type": "wiki", "name": "Wiki"}]  # note, add 'progress' when we can support it on Edge

    # a bit of a hack, but typically the "course image" which is shown on marketing pages is hard coded to /images/course_image.jpg
    # so let's make sure we import in case there are no other references to it in the modules
    verify_content_links(module, course_data_path, static_content_store, '/static/images/course_image.jpg')
    import_module_from_xml(modulestore, static_content_store, course_data_path, module, target_location_namespace, verbose=verbose)


def import_from_xml(store, data_dir, course_dirs=None,
                    default_class='xmodule.raw_module.RawDescriptor',
                    load_error_modules=True, static_content_store=None, target_location_namespace=None,
                    verbose=False, draft_store=None):
    """
    Import the specified xml data_dir into the "store" modulestore,
    using org and course as the location org and course.

    course_dirs: If specified, the list of course_dirs to load. Otherwise, load
    all course dirs

    target_location_namespace is the namespace [passed as Location] (i.e. {tag},{org},{course}) that all modules in the should be remapped to
    after import off disk. We do this remapping as a post-processing step because there's logic in the importing which
    expects a 'url_name' as an identifier to where things are on disk e.g. ../policies/<url_name>/policy.json as well as metadata keys in
    the policy.json. so we need to keep the original url_name during import

    """

    xml_module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        course_dirs=course_dirs,
        load_error_modules=load_error_modules
    )

    # NOTE: the XmlModuleStore does not implement get_items() which would be a preferable means
    # to enumerate the entire collection of course modules. It will be left as a TBD to implement that
    # method on XmlModuleStore.
    course_items = []
    for course_id in xml_module_store.modules.keys():

        if target_location_namespace is not None:
            pseudo_course_id = '/'.join([target_location_namespace.org, target_location_namespace.course])
        else:
            course_id_components = course_id.split('/')
            pseudo_course_id = '/'.join([course_id_components[0], course_id_components[1]])

        try:
            # turn off all write signalling while importing as this is a high volume operation
            if pseudo_course_id not in store.ignore_write_events_on_courses:
                store.ignore_write_events_on_courses.append(pseudo_course_id)

            course_data_path = None
            course_location = None

            if verbose:
                log.debug("Scanning {0} for course module...".format(course_id))

            # Quick scan to get course module as we need some info from there. Also we need to make sure that the
            # course module is committed first into the store
            for module in xml_module_store.modules[course_id].itervalues():
                if module.category == 'course':
                    course_data_path = path(data_dir) / module.data_dir
                    course_location = module.location

                    module = remap_namespace(module, target_location_namespace)

                    # cdodge: more hacks (what else). Seems like we have a problem when importing a course (like 6.002) which
                    # does not have any tabs defined in the policy file. The import goes fine and then displays fine in LMS,
                    # but if someone tries to add a new tab in the CMS, then the LMS barfs because it expects that -
                    # if there is *any* tabs - then there at least needs to be some predefined ones
                    if module.tabs is None or len(module.tabs) == 0:
                        module.tabs = [{"type": "courseware"},
                                       {"type": "course_info", "name": "Course Info"},
                                       {"type": "discussion", "name": "Discussion"},
                                       {"type": "wiki", "name": "Wiki"}]  # note, add 'progress' when we can support it on Edge

                    import_module(module, store, course_data_path, static_content_store)

                    # a bit of a hack, but typically the "course image" which is shown on marketing pages is hard coded to /images/course_image.jpg
                    # so let's make sure we import in case there are no other references to it in the modules
                    verify_content_links(module, course_data_path, static_content_store, '/static/images/course_image.jpg')

                    course_items.append(module)

            # then import all the static content
            if static_content_store is not None:
                _namespace_rename = target_location_namespace if target_location_namespace is not None else course_location

                # first pass to find everything in /static/
                import_static_content(xml_module_store.modules[course_id], course_location, course_data_path, static_content_store,
                                      _namespace_rename, subpath='static', verbose=verbose)

            # finally loop through all the modules
            for module in xml_module_store.modules[course_id].itervalues():

                if module.category == 'course':
                    # we've already saved the course module up at the top of the loop
                    # so just skip over it in the inner loop
                    continue

                # remap module to the new namespace
                if target_location_namespace is not None:
                    module = remap_namespace(module, target_location_namespace)

                if verbose:
                    log.debug('importing module location {0}'.format(module.location))

                import_module(module, store, course_data_path, static_content_store)

            # now import any 'draft' items
            if draft_store is not None:
                import_course_draft(xml_module_store, store, draft_store, course_data_path,
                                    static_content_store, target_location_namespace if target_location_namespace is not None
                                    else course_location)

        finally:
            # turn back on all write signalling
            if pseudo_course_id in store.ignore_write_events_on_courses:
                store.ignore_write_events_on_courses.remove(pseudo_course_id)
                store.refresh_cached_metadata_inheritance_tree(target_location_namespace if
                                                               target_location_namespace is not None else course_location)

    return xml_module_store, course_items


def import_module(module, store, course_data_path, static_content_store, allow_not_found=False):
    content = {}
    for field in module.fields:
        if field.scope != Scope.content:
            continue
        try:
            content[field.name] = module._model_data[field.name]
        except KeyError:
            # Ignore any missing keys in _model_data
            pass

    module_data = {}
    if 'data' in content:
        module_data = content['data']

        # cdodge: now go through any link references to '/static/' and make sure we've imported
        # it as a StaticContent asset
        try:
            remap_dict = {}

            # use the rewrite_links as a utility means to enumerate through all links
            # in the module data. We use that to load that reference into our asset store
            # IMPORTANT: There appears to be a bug in lxml.rewrite_link which makes us not be able to
            # do the rewrites natively in that code.
            # For example, what I'm seeing is <img src='foo.jpg' />   ->   <img src='bar.jpg'>
            # Note the dropped element closing tag. This causes the LMS to fail when rendering modules - that's
            # no good, so we have to do this kludge
            if isinstance(module_data, str) or isinstance(module_data, unicode):  # some module 'data' fields are non strings which blows up the link traversal code
                lxml_rewrite_links(module_data, lambda link: verify_content_links(module, course_data_path, static_content_store, link, remap_dict))

                for key in remap_dict.keys():
                    module_data = module_data.replace(key, remap_dict[key])

        except Exception:
            logging.exception("failed to rewrite links on {0}. Continuing...".format(module.location))
    else:
        module_data = content

    if allow_not_found:
        store.update_item(module.location, module_data, allow_not_found=allow_not_found)
    else:
        store.update_item(module.location, module_data)

    if hasattr(module, 'children') and module.children != []:
        store.update_children(module.location, module.children)

    # NOTE: It's important to use own_metadata here to avoid writing
    # inherited metadata everywhere.
    store.update_metadata(module.location, dict(own_metadata(module)))


def import_course_draft(xml_module_store, store, draft_store, course_data_path, static_content_store, target_location_namespace):
    '''
    This will import all the content inside of the 'drafts' folder, if it exists
    NOTE: This is not a full course import, basically in our current application only verticals (and downwards)
    can be in draft. Therefore, we need to use slightly different call points into the import process_xml
    as we can't simply call XMLModuleStore() constructor (like we do for importing public content)
    '''
    draft_dir = course_data_path + "/drafts"
    if not os.path.exists(draft_dir):
        return

    # create a new 'System' object which will manage the importing
    errorlog = make_error_tracker()
    system = ImportSystem(
        xml_module_store,
        target_location_namespace.course_id,
        draft_dir,
        {},
        errorlog.tracker,
        ParentTracker(),
        None,
    )

    # now walk the /vertical directory where each file in there will be a draft copy of the Vertical
    for dirname, dirnames, filenames in os.walk(draft_dir + "/vertical"):
        for filename in filenames:
            module_path = os.path.join(dirname, filename)
            with open(module_path) as f:
                try:
                    xml = f.read().decode('utf-8')
                    descriptor = system.process_xml(xml)

                    def _import_module(module):
                        module.location = module.location._replace(revision='draft')
                        # make sure our parent has us in its list of children
                        # this is to make sure private only verticals show up in the list of children since
                        # they would have been filtered out from the non-draft store export
                        if module.location.category == 'vertical':
                            module.location = module.location._replace(revision=None)
                            sequential_url = module.xml_attributes['parent_sequential_url']
                            index = int(module.xml_attributes['index_in_children_list'])

                            seq_location = Location(sequential_url)

                            # IMPORTANT: Be sure to update the sequential in the NEW namespace
                            seq_location = seq_location._replace(org=target_location_namespace.org,
                                                                 course=target_location_namespace.course
                                                                 )
                            sequential = store.get_item(seq_location)

                            if module.location.url() not in sequential.children:
                                sequential.children.insert(index, module.location.url())
                                store.update_children(sequential.location, sequential.children)

                            del module.xml_attributes['parent_sequential_url']
                            del module.xml_attributes['index_in_children_list']

                        import_module(module, draft_store, course_data_path, static_content_store, allow_not_found=True)
                        for child in module.get_children():
                            _import_module(child)

                    # HACK: since we are doing partial imports of drafts
                    # the vertical doesn't have the 'url-name' set in the attributes (they are normally in the parent
                    # object, aka sequential), so we have to replace the location.name with the XML filename
                    # that is part of the pack
                    fn, fileExtension = os.path.splitext(filename)
                    descriptor.location = descriptor.location._replace(name=fn)

                    _import_module(descriptor)

                except Exception, e:
                    logging.exception('There was an error. {0}'.format(unicode(e)))
                    pass


def remap_namespace(module, target_location_namespace):
    if target_location_namespace is None:
        return module

    # This looks a bit wonky as we need to also change the 'name' of the imported course to be what
    # the caller passed in
    if module.location.category != 'course':
        module.location = module.location._replace(tag=target_location_namespace.tag, org=target_location_namespace.org,
                                                   course=target_location_namespace.course)
    else:
        module.location = module.location._replace(tag=target_location_namespace.tag, org=target_location_namespace.org,
                                                   course=target_location_namespace.course, name=target_location_namespace.name)

    # then remap children pointers since they too will be re-namespaced
    if hasattr(module, 'children'):
        children_locs = module.children
        if children_locs is not None and children_locs != []:
            new_locs = []
            for child in children_locs:
                child_loc = Location(child)
                new_child_loc = child_loc._replace(tag=target_location_namespace.tag, org=target_location_namespace.org,
                                                   course=target_location_namespace.course)

                new_locs.append(new_child_loc.url())

            module.children = new_locs

    return module


def allowed_metadata_by_category(category):
    # should this be in the descriptors?!?
    return {
        'vertical': [],
        'chapter': ['start'],
        'sequential': ['due', 'format', 'start', 'graded']
    }.get(category, ['*'])


def check_module_metadata_editability(module):
    '''
    Assert that there is no metadata within a particular module that we can't support editing
    However we always allow 'display_name' and 'xml_attribtues'
    '''
    allowed = allowed_metadata_by_category(module.location.category)
    if '*' in allowed:
        # everything is allowed
        return 0

    allowed = allowed + ['xml_attributes', 'display_name']
    err_cnt = 0
    illegal_keys = set(own_metadata(module).keys()) - set(allowed)

    if len(illegal_keys) > 0:
        err_cnt = err_cnt + 1
        print ': found non-editable metadata on {0}. These metadata keys are not supported = {1}'. format(module.location.url(), illegal_keys)

    return err_cnt


def validate_no_non_editable_metadata(module_store, course_id, category):
    err_cnt = 0
    for module_loc in module_store.modules[course_id]:
        module = module_store.modules[course_id][module_loc]
        if module.location.category == category:
            err_cnt = err_cnt + check_module_metadata_editability(module)

    return err_cnt


def validate_category_hierarchy(module_store, course_id, parent_category, expected_child_category):
    err_cnt = 0

    parents = []
    # get all modules of parent_category
    for module in module_store.modules[course_id].itervalues():
        if module.location.category == parent_category:
            parents.append(module)

    for parent in parents:
        for child_loc in [Location(child) for child in parent.children]:
            if child_loc.category != expected_child_category:
                err_cnt += 1
                print 'ERROR: child {0} of parent {1} was expected to be category of {2} but was {3}'.format(
                    child_loc, parent.location, expected_child_category, child_loc.category)

    return err_cnt


def validate_data_source_path_existence(path, is_err=True, extra_msg=None):
    _cnt = 0
    if not os.path.exists(path):
        print ("{0}: Expected folder at {1}. {2}".format('ERROR' if is_err == True else 'WARNING', path, extra_msg if
               extra_msg is not None else ''))
        _cnt = 1
    return _cnt


def validate_data_source_paths(data_dir, course_dir):
    # check that there is a '/static/' directory
    course_path = data_dir / course_dir
    err_cnt = 0
    warn_cnt = 0
    err_cnt += validate_data_source_path_existence(course_path / 'static')
    warn_cnt += validate_data_source_path_existence(course_path / 'static/subs', is_err=False,
                                                    extra_msg='Video captions (if they are used) will not work unless they are static/subs.')
    return err_cnt, warn_cnt


def validate_course_policy(module_store, course_id):
    """
    Validate that the course explicitly sets values for any fields whose defaults may have changed between
    the export and the import.

    Does not add to error count as these are just warnings.
    """
    # is there a reliable way to get the module location just given the course_id?
    warn_cnt = 0
    for module in module_store.modules[course_id].itervalues():
        if module.location.category == 'course':
            if not 'rerandomize' in module._model_data:
                warn_cnt += 1
                print 'WARN: course policy does not specify value for "rerandomize" whose default is now "never". The behavior of your course may change.'
            if not 'showanswer' in module._model_data:
                warn_cnt += 1
                print 'WARN: course policy does not specify value for "showanswer" whose default is now "finished". The behavior of your course may change.'
    return warn_cnt


def perform_xlint(data_dir, course_dirs,
                  default_class='xmodule.raw_module.RawDescriptor',
                  load_error_modules=True):
    err_cnt = 0
    warn_cnt = 0

    module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        course_dirs=course_dirs,
        load_error_modules=load_error_modules
    )

    # check all data source path information
    for course_dir in course_dirs:
        _err_cnt, _warn_cnt = validate_data_source_paths(path(data_dir), course_dir)
        err_cnt += _err_cnt
        warn_cnt += _warn_cnt

    # first count all errors and warnings as part of the XMLModuleStore import
    for err_log in module_store._location_errors.itervalues():
        for err_log_entry in err_log.errors:
            msg = err_log_entry[0]
            if msg.startswith('ERROR:'):
                err_cnt += 1
            else:
                warn_cnt += 1

    # then count outright all courses that failed to load at all
    for err_log in module_store.errored_courses.itervalues():
        for err_log_entry in err_log.errors:
            msg = err_log_entry[0]
            print msg
            if msg.startswith('ERROR:'):
                err_cnt += 1
            else:
                warn_cnt += 1

    for course_id in module_store.modules.keys():
        # constrain that courses only have 'chapter' children
        err_cnt += validate_category_hierarchy(module_store, course_id, "course", "chapter")
        # constrain that chapters only have 'sequentials'
        err_cnt += validate_category_hierarchy(module_store, course_id, "chapter", "sequential")
        # constrain that sequentials only have 'verticals'
        err_cnt += validate_category_hierarchy(module_store, course_id, "sequential", "vertical")
        # validate the course policy overrides any defaults which have changed over time
        warn_cnt += validate_course_policy(module_store, course_id)
        # don't allow metadata on verticals, since we can't edit them in studio
        err_cnt += validate_no_non_editable_metadata(module_store, course_id, "vertical")
        # don't allow metadata on chapters, since we can't edit them in studio
        err_cnt += validate_no_non_editable_metadata(module_store, course_id, "chapter")
        # don't allow metadata on sequences that we can't edit
        err_cnt += validate_no_non_editable_metadata(module_store, course_id, "sequential")

        # check for a presence of a course marketing video
        location_elements = course_id.split('/')
        if Location(['i4x', location_elements[0], location_elements[1], 'about', 'video', None]) not in module_store.modules[course_id]:
            print "WARN: Missing course marketing video. It is recommended that every course have a marketing video."
            warn_cnt += 1

    print "\n\n------------------------------------------\nVALIDATION SUMMARY: {0} Errors   {1} Warnings\n".format(err_cnt, warn_cnt)

    if err_cnt > 0:
        print "This course is not suitable for importing. Please fix courseware according to specifications before importing."
    elif warn_cnt > 0:
        print "This course can be imported, but some errors may occur during the run of the course. It is recommend that you fix your courseware before importing"
    else:
        print "This course can be imported successfully."

    return err_cnt
