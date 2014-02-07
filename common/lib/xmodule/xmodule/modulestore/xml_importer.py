import logging
import os
import mimetypes
from path import path
import json

from xblock.fields import Scope

from .xml import XMLModuleStore, ImportSystem, ParentTracker
from xmodule.modulestore import Location
from xmodule.contentstore.content import StaticContent
from .inheritance import own_metadata
from xmodule.errortracker import make_error_tracker
from .store_utilities import rewrite_nonportable_content_links

log = logging.getLogger(__name__)


def import_static_content(
        modules, course_loc, course_data_path, static_content_store,
        target_location_namespace, subpath='static', verbose=False):

    remap_dict = {}

    # now import all static assets
    static_dir = course_data_path / subpath
    try:
        with open(course_data_path / 'policies/assets.json') as f:
            policy = json.load(f)
    except (IOError, ValueError) as err:
        # xml backed courses won't have this file, only exported courses;
        # so, its absence is not really an exception.
        policy = {}

    verbose = True
    mimetypes_list = mimetypes.types_map.values()

    for dirname, _, filenames in os.walk(static_dir):
        for filename in filenames:

            content_path = os.path.join(dirname, filename)

            if filename.endswith('~'):
                if verbose:
                    log.debug('skipping static content %s...', content_path)
                continue

            if verbose:
                log.debug('importing static content %s...', content_path)

            try:
                with open(content_path, 'rb') as f:
                    data = f.read()
            except IOError:
                if filename.startswith('._'):
                    # OS X "companion files". See
                    # http://www.diigo.com/annotated/0c936fda5da4aa1159c189cea227e174
                    continue
                # Not a 'hidden file', then re-raise exception
                raise

            # strip away leading path from the name
            fullname_with_subpath = content_path.replace(static_dir, '')
            if fullname_with_subpath.startswith('/'):
                fullname_with_subpath = fullname_with_subpath[1:]
            content_loc = StaticContent.compute_location(
                target_location_namespace.org, target_location_namespace.course,
                fullname_with_subpath
            )

            policy_ele = policy.get(content_loc.name, {})
            displayname = policy_ele.get('displayname', filename)
            locked = policy_ele.get('locked', False)
            mime_type = policy_ele.get('contentType')

            # Check extracted contentType in list of all valid mimetypes
            if not mime_type or mime_type not in mimetypes_list:
                mime_type = mimetypes.guess_type(filename)[0]   # Assign guessed mimetype
            content = StaticContent(
                content_loc, displayname, mime_type, data,
                import_path=fullname_with_subpath, locked=locked
            )

            # first let's save a thumbnail so we can get back a thumbnail location
            thumbnail_content, thumbnail_location = static_content_store.generate_thumbnail(content)

            if thumbnail_content is not None:
                content.thumbnail_location = thumbnail_location

            # then commit the content
            try:
                static_content_store.save(content)
            except Exception as err:
                log.exception('Error importing {0}, error={1}'.format(
                    fullname_with_subpath, err
                ))

            # store the remapping information which will be needed
            # to subsitute in the module data
            remap_dict[fullname_with_subpath] = content_loc.name

    return remap_dict


def import_from_xml(
        store, data_dir, course_dirs=None,
        default_class='xmodule.raw_module.RawDescriptor',
        load_error_modules=True, static_content_store=None,
        target_location_namespace=None, verbose=False, draft_store=None,
        do_import_static=True):
    """
    Import the specified xml data_dir into the "store" modulestore,
    using org and course as the location org and course.

    course_dirs: If specified, the list of course_dirs to load. Otherwise, load
    all course dirs

    target_location_namespace is the namespace [passed as Location]
    (i.e. {tag},{org},{course}) that all modules in the should be remapped to
    after import off disk. We do this remapping as a post-processing step
    because there's logic in the importing which expects a 'url_name' as an
    identifier to where things are on disk
    e.g. ../policies/<url_name>/policy.json as well as metadata keys in
    the policy.json. so we need to keep the original url_name during import

    :param do_import_static:
        if False, then static files are not imported into the static content
        store. This can be employed for courses which have substantial
        unchanging static content, which is to inefficient to import every
        time the course is loaded. Static content for some courses may also be
        served directly by nginx, instead of going through django.

    """

    xml_module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        course_dirs=course_dirs,
        load_error_modules=load_error_modules,
        xblock_mixins=store.xblock_mixins,
        xblock_select=store.xblock_select,
    )

    # NOTE: the XmlModuleStore does not implement get_items()
    # which would be a preferable means to enumerate the entire collection
    # of course modules. It will be left as a TBD to implement that
    # method on XmlModuleStore.
    course_items = []
    for course_id in xml_module_store.modules.keys():

        if target_location_namespace is not None:
            pseudo_course_id = '/'.join(
                [target_location_namespace.org, target_location_namespace.course]
            )
        else:
            course_id_components = course_id.split('/')
            pseudo_course_id = '/'.join(
                [course_id_components[0], course_id_components[1]]
            )

        try:
            # turn off all write signalling while importing as this
            # is a high volume operation on stores that need it
            if (hasattr(store, 'ignore_write_events_on_courses') and
                    pseudo_course_id not in store.ignore_write_events_on_courses):
                store.ignore_write_events_on_courses.append(pseudo_course_id)

            course_data_path = None
            course_location = None

            if verbose:
                log.debug("Scanning {0} for course module...".format(course_id))

            # Quick scan to get course module as we need some info from there.
            # Also we need to make sure that the course module is committed
            # first into the store
            for module in xml_module_store.modules[course_id].itervalues():
                if module.scope_ids.block_type == 'course':
                    course_data_path = path(data_dir) / module.data_dir
                    course_location = module.location

                    log.debug('======> IMPORTING course to location {loc}'.format(
                        loc=course_location
                    ))

                    module = remap_namespace(module, target_location_namespace)

                    if not do_import_static:
                        # for old-style xblock where this was actually linked to kvs
                        module.static_asset_path = module.data_dir
                        module.save()
                        log.debug('course static_asset_path={path}'.format(
                            path=module.static_asset_path
                        ))

                    log.debug('course data_dir={0}'.format(module.data_dir))

                    # cdodge: more hacks (what else). Seems like we have a
                    # problem when importing a course (like 6.002) which
                    # does not have any tabs defined in the policy file.
                    # The import goes fine and then displays fine in LMS,
                    # but if someone tries to add a new tab in the CMS, then
                    # the LMS barfs because it expects that -- if there are
                    # *any* tabs -- then there at least needs to be
                    # some predefined ones
                    if module.tabs is None or len(module.tabs) == 0:
                        module.tabs = [
                            {"type": "courseware"},
                            {"type": "course_info", "name": "Course Info"},
                            {"type": "discussion", "name": "Discussion"},
                            {"type": "wiki", "name": "Wiki"},
                            # note, add 'progress' when we can support it on Edge
                        ]

                    import_module(
                        module, store, course_data_path, static_content_store,
                        course_location,
                        target_location_namespace or course_location,
                        do_import_static=do_import_static
                    )

                    course_items.append(module)

            # then import all the static content
            if static_content_store is not None and do_import_static:
                if target_location_namespace is not None:
                    _namespace_rename = target_location_namespace
                else:
                    _namespace_rename = course_location

                # first pass to find everything in /static/
                import_static_content(
                    xml_module_store.modules[course_id], course_location,
                    course_data_path, static_content_store,
                    _namespace_rename, subpath='static', verbose=verbose
                )

            elif verbose and not do_import_static:
                log.debug(
                    "Skipping import of static content, "
                    "since do_import_static={0}".format(do_import_static)
                )

            # no matter what do_import_static is, import "static_import" directory

            # This is needed because the "about" pages (eg "overview") are
            # loaded via load_extra_content, and do not inherit the lms
            # metadata from the course module, and thus do not get
            # "static_content_store" properly defined. Static content
            # referenced in those extra pages thus need to come through the
            # c4x:// contentstore, unfortunately. Tell users to copy that
            # content into the "static_import" subdir.

            simport = 'static_import'
            if os.path.exists(course_data_path / simport):
                if target_location_namespace is not None:
                    _namespace_rename = target_location_namespace
                else:
                    _namespace_rename = course_location

                import_static_content(
                    xml_module_store.modules[course_id], course_location,
                    course_data_path, static_content_store,
                    _namespace_rename, subpath=simport, verbose=verbose
                )

            # finally loop through all the modules
            for module in xml_module_store.modules[course_id].itervalues():
                if module.scope_ids.block_type == 'course':
                    # we've already saved the course module up at the top
                    # of the loop so just skip over it in the inner loop
                    continue

                # remap module to the new namespace
                if target_location_namespace is not None:
                    module = remap_namespace(module, target_location_namespace)

                if verbose:
                    log.debug('importing module location {loc}'.format(
                        loc=module.location
                    ))

                import_module(
                    module, store, course_data_path, static_content_store,
                    course_location,
                    target_location_namespace if target_location_namespace else course_location,
                    do_import_static=do_import_static
                )

            # now import any 'draft' items
            if draft_store is not None:
                import_course_draft(
                    xml_module_store,
                    store,
                    draft_store,
                    course_data_path,
                    static_content_store,
                    course_location,
                    target_location_namespace if target_location_namespace else course_location
                )

        finally:
            # turn back on all write signalling on stores that need it
            if (hasattr(store, 'ignore_write_events_on_courses') and
                    pseudo_course_id in store.ignore_write_events_on_courses):
                store.ignore_write_events_on_courses.remove(pseudo_course_id)
                store.refresh_cached_metadata_inheritance_tree(
                    target_location_namespace if target_location_namespace is not None else course_location
                )

    return xml_module_store, course_items


def import_module(
        module, store, course_data_path, static_content_store,
        source_course_location, dest_course_location, allow_not_found=False,
        do_import_static=True):

    logging.debug('processing import of module {}...'.format(module.location.url()))

    content = {}
    for field in module.fields.values():
        if field.scope != Scope.content:
            continue
        try:
            content[field.name] = module._field_data.get(module, field.name)
        except KeyError:
            # Ignore any missing keys in _field_data
            pass

    module_data = {}
    if 'data' in content:
        module_data = content['data']
    else:
        module_data = content

    if isinstance(module_data, basestring) and do_import_static:
        # we want to convert all 'non-portable' links in the module_data
        # (if it is a string) to portable strings (e.g. /static/)
        module_data = rewrite_nonportable_content_links(
            source_course_location.course_id,
            dest_course_location.course_id, module_data
        )

    if allow_not_found:
        store.update_item(
            module.location, module_data, allow_not_found=allow_not_found
        )
    else:
        store.update_item(module.location, module_data)

    if hasattr(module, 'children') and module.children != []:
        store.update_children(module.location, module.children)

    # NOTE: It's important to use own_metadata here to avoid writing
    # inherited metadata everywhere.

    # remove any export/import only xml_attributes
    # which are used to wire together draft imports
    if 'parent_sequential_url' in getattr(module, 'xml_attributes', []):
        del module.xml_attributes['parent_sequential_url']

    if 'index_in_children_list' in getattr(module, 'xml_attributes', []):
        del module.xml_attributes['index_in_children_list']
    module.save()

    store.update_metadata(module.location, dict(own_metadata(module)))


def import_course_draft(
        xml_module_store, store, draft_store, course_data_path,
        static_content_store, source_location_namespace,
        target_location_namespace):
    '''
    This will import all the content inside of the 'drafts' folder, if it exists
    NOTE: This is not a full course import, basically in our current
    application only verticals (and downwards) can be in draft.
    Therefore, we need to use slightly different call points into
    the import process_xml as we can't simply call XMLModuleStore() constructor
    (like we do for importing public content)
    '''
    draft_dir = course_data_path + "/drafts"
    if not os.path.exists(draft_dir):
        return

    # create a new 'System' object which will manage the importing
    errorlog = make_error_tracker()

    # The course_dir as passed to ImportSystem is expected to just be relative, not
    # the complete path including data_dir. ImportSystem will concatenate the two together.
    data_dir = xml_module_store.data_dir
    # Whether or not data_dir ends with a "/" differs in production vs. test.
    if not data_dir.endswith("/"):
        data_dir += "/"
    draft_course_dir = draft_dir.replace(data_dir, '', 1)
    system = ImportSystem(
        xmlstore=xml_module_store,
        course_id=target_location_namespace.course_id,
        course_dir=draft_course_dir,
        error_tracker=errorlog.tracker,
        parent_tracker=ParentTracker(),
        load_error_modules=False,
        field_data=None,
    )

    # now walk the /vertical directory where each file in there
    # will be a draft copy of the Vertical

    # First it is necessary to order the draft items by their desired index in the child list
    # (order os.walk returns them in is not guaranteed).
    drafts = dict()
    for dirname, dirnames, filenames in os.walk(draft_dir + "/vertical"):
        for filename in filenames:
            module_path = os.path.join(dirname, filename)
            with open(module_path, 'r') as f:
                try:
                    # note, on local dev it seems like OSX will put
                    # some extra files in the directory with "quarantine"
                    # information. These files are binary files and will
                    # throw exceptions when we try to parse the file
                    # as an XML string. Let's make sure we're
                    # dealing with a string before ingesting
                    data = f.read()

                    try:
                        xml = data.decode('utf-8')
                    except UnicodeDecodeError, err:
                        # seems like on OSX localdev, the OS is making
                        # quarantine files in the unzip directory
                        # when importing courses so if we blindly try to
                        # enumerate through the directory, we'll try
                        # to process a bunch of binary quarantine files
                        # (which are prefixed with a '._' character which
                        # will dump a bunch of exceptions to the output,
                        # although they are harmless.
                        #
                        # Reading online docs there doesn't seem to be
                        # a good means to detect a 'hidden' file that works
                        # well across all OS environments. So for now, I'm using
                        # OSX's utilization of a leading '.' in the filename
                        # to indicate a system hidden file.
                        #
                        # Better yet would be a way to figure out if this is
                        # a binary file, but I haven't found a good way
                        # to do this yet.
                        if filename.startswith('._'):
                            continue
                        # Not a 'hidden file', then re-raise exception
                        raise err

                    descriptor = system.process_xml(xml)

                    # HACK: since we are doing partial imports of drafts
                    # the vertical doesn't have the 'url-name' set in the
                    # attributes (they are normally in the parent object,
                    # aka sequential), so we have to replace the location.name
                    # with the XML filename that is part of the pack
                    fn, fileExtension = os.path.splitext(filename)
                    descriptor.location = descriptor.location._replace(name=fn)

                    index = int(descriptor.xml_attributes['index_in_children_list'])
                    if index in drafts:
                        drafts[index].append(descriptor)
                    else:
                        drafts[index] = [descriptor]

                except Exception, e:
                    logging.exception('There was an error. {err}'.format(
                        err=unicode(e)
                    ))

        # For each index_in_children_list key, there is a list of vertical descriptors.
        for key in sorted(drafts.iterkeys()):
            for descriptor in drafts[key]:
                try:
                    def _import_module(module):
                        module.location = module.location._replace(revision='draft')
                        # make sure our parent has us in its list of children
                        # this is to make sure private only verticals show up
                        # in the list of children since they would have been
                        # filtered out from the non-draft store export
                        if module.location.category == 'vertical':
                            non_draft_location = module.location._replace(revision=None)
                            sequential_url = module.xml_attributes['parent_sequential_url']
                            index = int(module.xml_attributes['index_in_children_list'])

                            seq_location = Location(sequential_url)

                            # IMPORTANT: Be sure to update the sequential
                            # in the NEW namespace
                            seq_location = seq_location._replace(
                                org=target_location_namespace.org,
                                course=target_location_namespace.course
                            )
                            sequential = store.get_item(seq_location, depth=0)

                            if non_draft_location.url() not in sequential.children:
                                sequential.children.insert(index, non_draft_location.url())
                                store.update_children(sequential.location, sequential.children)

                        import_module(
                            module, draft_store, course_data_path,
                            static_content_store, source_location_namespace,
                            target_location_namespace, allow_not_found=True
                        )
                        for child in module.get_children():
                            _import_module(child)

                    _import_module(descriptor)

                except Exception, e:
                    logging.exception('There was an error. {err}'.format(
                        err=unicode(e)
                    ))


def remap_namespace(module, target_location_namespace):
    if target_location_namespace is None:
        return module

    # This looks a bit wonky as we need to also change the 'name' of the
    # imported course to be what the caller passed in
    if module.location.category != 'course':
        module.location = module.location._replace(
            tag=target_location_namespace.tag,
            org=target_location_namespace.org,
            course=target_location_namespace.course
        )
    else:
        original_location = module.location
        #
        # module is a course module
        #
        module.location = module.location._replace(
            tag=target_location_namespace.tag,
            org=target_location_namespace.org,
            course=target_location_namespace.course,
            name=target_location_namespace.name
        )
        # There is more re-namespacing work we have to do when
        # importing course modules

        # remap pdf_textbook urls
        for entry in module.pdf_textbooks:
            for chapter in entry.get('chapters', []):
                if StaticContent.is_c4x_path(chapter.get('url', '')):
                    chapter['url'] = StaticContent.renamespace_c4x_path(
                        chapter['url'], target_location_namespace
                    )

        # if there is a wiki_slug which is the same as the original location
        # (aka default value), then remap that so the wiki doesn't point to
        # the old Wiki.
        if module.wiki_slug == original_location.course:
            module.wiki_slug = target_location_namespace.course

        module.save()

    # then remap children pointers since they too will be re-namespaced
    if hasattr(module, 'children'):
        children_locs = module.children
        if children_locs is not None and children_locs != []:
            new_locs = []
            for child in children_locs:
                child_loc = Location(child)
                new_child_loc = child_loc._replace(
                    tag=target_location_namespace.tag,
                    org=target_location_namespace.org,
                    course=target_location_namespace.course
                )

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
    Assert that there is no metadata within a particular module that
    we can't support editing. However we always allow 'display_name'
    and 'xml_attributes'
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
        print(
            ": found non-editable metadata on {url}. "
            "These metadata keys are not supported = {keys}".format(
                url=module.location.url(), keys=illegal_keys
            )
        )

    return err_cnt


def validate_no_non_editable_metadata(module_store, course_id, category):
    err_cnt = 0
    for module_loc in module_store.modules[course_id]:
        module = module_store.modules[course_id][module_loc]
        if module.location.category == category:
            err_cnt = err_cnt + check_module_metadata_editability(module)

    return err_cnt


def validate_category_hierarchy(
        module_store, course_id, parent_category, expected_child_category):
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
                print(
                    "ERROR: child {child} of parent {parent} was expected to be "
                    "category of {expected} but was {actual}".format(
                        child=child_loc, parent=parent.location,
                        expected=expected_child_category,
                        actual=child_loc.category
                    )
                )

    return err_cnt


def validate_data_source_path_existence(path, is_err=True, extra_msg=None):
    _cnt = 0
    if not os.path.exists(path):
        print(
            "{type}: Expected folder at {path}. {extra}".format(
                type='ERROR' if is_err else 'WARNING',
                path=path,
                extra=extra_msg or "",
            )
        )
        _cnt = 1
    return _cnt


def validate_data_source_paths(data_dir, course_dir):
    # check that there is a '/static/' directory
    course_path = data_dir / course_dir
    err_cnt = 0
    warn_cnt = 0
    err_cnt += validate_data_source_path_existence(course_path / 'static')
    warn_cnt += validate_data_source_path_existence(
        course_path / 'static/subs', is_err=False,
        extra_msg='Video captions (if they are used) will not work unless they are static/subs.'
    )
    return err_cnt, warn_cnt


def validate_course_policy(module_store, course_id):
    """
    Validate that the course explicitly sets values for any fields
    whose defaults may have changed between the export and the import.

    Does not add to error count as these are just warnings.
    """
    # is there a reliable way to get the module location just given the course_id?
    warn_cnt = 0
    for module in module_store.modules[course_id].itervalues():
        if module.location.category == 'course':
            if not module._field_data.has(module, 'rerandomize'):
                warn_cnt += 1
                print(
                    'WARN: course policy does not specify value for '
                    '"rerandomize" whose default is now "never". '
                    'The behavior of your course may change.'
                )
            if not module._field_data.has(module, 'showanswer'):
                warn_cnt += 1
                print(
                    'WARN: course policy does not specify value for '
                    '"showanswer" whose default is now "finished". '
                    'The behavior of your course may change.'
                )
    return warn_cnt


def perform_xlint(
        data_dir, course_dirs,
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
            print(msg)
            if msg.startswith('ERROR:'):
                err_cnt += 1
            else:
                warn_cnt += 1

    for course_id in module_store.modules.keys():
        # constrain that courses only have 'chapter' children
        err_cnt += validate_category_hierarchy(
            module_store, course_id, "course", "chapter"
        )
        # constrain that chapters only have 'sequentials'
        err_cnt += validate_category_hierarchy(
            module_store, course_id, "chapter", "sequential"
        )
        # constrain that sequentials only have 'verticals'
        err_cnt += validate_category_hierarchy(
            module_store, course_id, "sequential", "vertical"
        )
        # validate the course policy overrides any defaults
        # which have changed over time
        warn_cnt += validate_course_policy(module_store, course_id)
        # don't allow metadata on verticals, since we can't edit them in studio
        err_cnt += validate_no_non_editable_metadata(
            module_store, course_id, "vertical"
        )
        # don't allow metadata on chapters, since we can't edit them in studio
        err_cnt += validate_no_non_editable_metadata(
            module_store, course_id, "chapter"
        )
        # don't allow metadata on sequences that we can't edit
        err_cnt += validate_no_non_editable_metadata(
            module_store, course_id, "sequential"
        )

        # check for a presence of a course marketing video
        location_elements = course_id.split('/')
        loc = Location([
            'i4x', location_elements[0], location_elements[1],
            'about', 'video', None
        ])
        if loc not in module_store.modules[course_id]:
            print(
                "WARN: Missing course marketing video. It is recommended "
                "that every course have a marketing video."
            )
            warn_cnt += 1

    print("\n")
    print("------------------------------------------")
    print("VALIDATION SUMMARY: {err} Errors   {warn} Warnings".format(
        err=err_cnt, warn=warn_cnt)
    )

    if err_cnt > 0:
        print(
            "This course is not suitable for importing. Please fix courseware "
            "according to specifications before importing."
        )
    elif warn_cnt > 0:
        print(
            "This course can be imported, but some errors may occur "
            "during the run of the course. It is recommend that you fix "
            "your courseware before importing"
        )
    else:
        print("This course can be imported successfully.")

    return err_cnt
