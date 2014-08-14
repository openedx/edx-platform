"""
Each store has slightly different semantics wrt draft v published. XML doesn't officially recognize draft
but does hold it in a subdir. Old mongo has a virtual but not physical draft for every unit in published state.
Split mongo has a physical for every unit in every state.

Given that, here's a table of semantics and behaviors where - means no record and letters indicate values.
For xml, (-, x) means the item is published and can be edited. For split, it means the item's
been deleted from draft and will be deleted from published the next time it gets published. old mongo
can't represent that virtual state (2nd row in table)

In the table body, the tuples represent virtual modulestore result. The row headers represent the pre-import
modulestore state.

Modulestore virtual   |          XML physical (draft, published)
(draft, published)    |  (-, -) | (x, -) | (x, x) | (x, y) | (-, x)
----------------------+--------------------------------------------
             (-, -)   |  (-, -) | (x, -) | (x, x) | (x, y) | (-, x)
             (-, a)   |  (-, a) | (x, a) | (x, x) | (x, y) | (-, x) : deleted from draft before import
             (a, -)   |  (a, -) | (x, -) | (x, x) | (x, y) | (a, x)
             (a, a)   |  (a, a) | (x, a) | (x, x) | (x, y) | (a, x)
             (a, b)   |  (a, b) | (x, b) | (x, x) | (x, y) | (a, x)
"""
import logging
import os
import mimetypes
from path import path
import json
import re

from .xml import XMLModuleStore, ImportSystem, ParentTracker
from xblock.runtime import KvsFieldData, DictKeyValueStore
from xmodule.x_module import XModuleDescriptor
from opaque_keys.edx.keys import UsageKey
from xblock.fields import Scope, Reference, ReferenceList, ReferenceValueDict
from xmodule.contentstore.content import StaticContent
from .inheritance import own_metadata
from xmodule.errortracker import make_error_tracker
from .store_utilities import rewrite_nonportable_content_links
import xblock
from xmodule.tabs import CourseTabList
from xmodule.modulestore.django import ASSET_IGNORE_REGEX
from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore.mongo.base import MongoRevisionKey
from xmodule.modulestore import ModuleStoreEnum

log = logging.getLogger(__name__)


def import_static_content(
        course_data_path, static_content_store,
        target_course_id, subpath='static', verbose=False):

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

    mimetypes.add_type('application/octet-stream', '.sjson')
    mimetypes.add_type('application/octet-stream', '.srt')
    mimetypes_list = mimetypes.types_map.values()

    for dirname, _, filenames in os.walk(static_dir):
        for filename in filenames:

            content_path = os.path.join(dirname, filename)

            if re.match(ASSET_IGNORE_REGEX, filename):
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
            asset_key = StaticContent.compute_location(target_course_id, fullname_with_subpath)

            policy_ele = policy.get(asset_key.path, {})
            displayname = policy_ele.get('displayname', filename)
            locked = policy_ele.get('locked', False)
            mime_type = policy_ele.get('contentType')

            # Check extracted contentType in list of all valid mimetypes
            if not mime_type or mime_type not in mimetypes_list:
                mime_type = mimetypes.guess_type(filename)[0]   # Assign guessed mimetype
            content = StaticContent(
                asset_key, displayname, mime_type, data,
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
                log.exception(u'Error importing {0}, error={1}'.format(
                    fullname_with_subpath, err
                ))

            # store the remapping information which will be needed
            # to subsitute in the module data
            remap_dict[fullname_with_subpath] = asset_key

    return remap_dict


def import_from_xml(
        store, user_id, data_dir, course_dirs=None,
        default_class='xmodule.raw_module.RawDescriptor',
        load_error_modules=True, static_content_store=None,
        target_course_id=None, verbose=False,
        do_import_static=True, create_new_course_if_not_present=False):
    """
    Import xml-based courses from data_dir into modulestore.

    Returns:
        list of new course objects

    Args:
        store: a modulestore implementing ModuleStoreWriteBase in which to store the imported courses.

        data_dir: the root directory from which to find the xml courses.

        course_dirs: If specified, the list of data_dir subdirectories to load. Otherwise, load
            all course dirs

        target_course_id: is the CourseKey that all modules should be remapped to
            after import off disk. NOTE: this only makes sense if importing only
            one course. If there are more than one course loaded from data_dir/course_dirs & you
            supply this id, this method will raise an AssertException.

        static_content_store: the static asset store

        do_import_static: if True, then import the course's static files into static_content_store
            This can be employed for courses which have substantial
            unchanging static content, which is too inefficient to import every
            time the course is loaded. Static content for some courses may also be
            served directly by nginx, instead of going through django.

        create_new_course_if_not_present: If True, then a new course is created if it doesn't already exist.
            Otherwise, it throws an InvalidLocationError if the course does not exist.

        default_class, load_error_modules: are arguments for constructing the XMLModuleStore (see its doc)
    """

    xml_module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        course_dirs=course_dirs,
        load_error_modules=load_error_modules,
        xblock_mixins=store.xblock_mixins,
        xblock_select=store.xblock_select,
    )

    # If we're going to remap the course_id, then we can only do that with
    # a single course
    if target_course_id:
        assert(len(xml_module_store.modules) == 1)

    new_courses = []
    for course_key in xml_module_store.modules.keys():
        if target_course_id is not None:
            dest_course_id = target_course_id
        else:
            dest_course_id = store.make_course_key(course_key.org, course_key.course, course_key.run)

        runtime = None
        # Creates a new course if it doesn't already exist
        if create_new_course_if_not_present and not store.has_course(dest_course_id, ignore_case=True):
            try:
                new_course = store.create_course(dest_course_id.org, dest_course_id.course, dest_course_id.run, user_id)
                runtime = new_course.runtime
            except DuplicateCourseError:
                # course w/ same org and course exists
                log.debug(
                    "Skipping import of course with id, %s,"
                    "since it collides with an existing one", dest_course_id
                )
                continue

        with store.bulk_write_operations(dest_course_id):
            source_course = xml_module_store.get_course(course_key)
            # STEP 1: find and import course module
            course, course_data_path = _import_course_module(
                store, runtime, user_id,
                data_dir, course_key, dest_course_id, source_course,
                do_import_static, verbose
            )
            new_courses.append(course)

            # STEP 2: import static content
            _import_static_content_wrapper(
                static_content_store, do_import_static, course_data_path, dest_course_id, verbose
            )

            # STEP 3: import PUBLISHED items
            # now loop through all the modules depth first and then orphans
            with store.branch_setting(ModuleStoreEnum.Branch.published_only, dest_course_id):
                all_locs = set(xml_module_store.modules[course_key].keys())
                all_locs.remove(source_course.location)

                def depth_first(subtree):
                    """
                    Import top down just so import code can make assumptions about parents always being available
                    """
                    if subtree.has_children:
                        for child in subtree.get_children():
                            try:
                                all_locs.remove(child.location)
                            except KeyError:
                                # tolerate same child occurring under 2 parents such as in
                                # ContentStoreTest.test_image_import
                                pass
                            if verbose:
                                log.debug('importing module location {loc}'.format(loc=child.location))

                            _import_module_and_update_references(
                                child,
                                store,
                                user_id,
                                course_key,
                                dest_course_id,
                                do_import_static=do_import_static,
                                runtime=course.runtime
                            )
                            depth_first(child)

                depth_first(source_course)

                for leftover in all_locs:
                    if verbose:
                        log.debug('importing module location {loc}'.format(loc=leftover))

                    _import_module_and_update_references(
                        xml_module_store.get_item(leftover), store,
                        user_id,
                        course_key,
                        dest_course_id,
                        do_import_static=do_import_static,
                        runtime=course.runtime
                    )

            # STEP 4: import any DRAFT items
            with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, dest_course_id):
                _import_course_draft(
                    xml_module_store,
                    store,
                    user_id,
                    course_data_path,
                    course_key,
                    dest_course_id,
                    course.runtime
                )

    return new_courses


def _import_course_module(
        store, runtime, user_id, data_dir, course_key, dest_course_id, source_course, do_import_static,
        verbose,
):
    if verbose:
        log.debug("Scanning {0} for course module...".format(course_key))

    # Quick scan to get course module as we need some info from there.
    # Also we need to make sure that the course module is committed
    # first into the store
    course_data_path = path(data_dir) / source_course.data_dir

    log.debug(u'======> IMPORTING course {course_key}'.format(
        course_key=course_key,
    ))

    if not do_import_static:
        # for old-style xblock where this was actually linked to kvs
        source_course.static_asset_path = source_course.data_dir
        source_course.save()
        log.debug('course static_asset_path={path}'.format(
            path=source_course.static_asset_path
        ))

    log.debug('course data_dir={0}'.format(source_course.data_dir))

    with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, dest_course_id):

        course = _import_module_and_update_references(
            source_course, store, user_id,
            course_key,
            dest_course_id,
            do_import_static=do_import_static,
            runtime=runtime,
        )

        for entry in course.pdf_textbooks:
            for chapter in entry.get('chapters', []):
                if StaticContent.is_c4x_path(chapter.get('url', '')):
                    asset_key = StaticContent.get_location_from_path(chapter['url'])
                    chapter['url'] = StaticContent.get_static_path_from_location(asset_key)

        # Original wiki_slugs had value location.course. To make them unique this was changed to 'org.course.name'.
        # If we are importing into a course with a different course_id and wiki_slug is equal to either of these default
        # values then remap it so that the wiki does not point to the old wiki.
        if course_key != course.id:
            original_unique_wiki_slug = u'{0}.{1}.{2}'.format(
                course_key.org,
                course_key.course,
                course_key.run
            )
            if course.wiki_slug == original_unique_wiki_slug or course.wiki_slug == course_key.course:
                course.wiki_slug = u'{0}.{1}.{2}'.format(
                    course.id.org,
                    course.id.course,
                    course.id.run,
                )

        # cdodge: more hacks (what else). Seems like we have a
        # problem when importing a course (like 6.002) which
        # does not have any tabs defined in the policy file.
        # The import goes fine and then displays fine in LMS,
        # but if someone tries to add a new tab in the CMS, then
        # the LMS barfs because it expects that -- if there are
        # *any* tabs -- then there at least needs to be
        # some predefined ones
        if course.tabs is None or len(course.tabs) == 0:
            CourseTabList.initialize_default(course)

        store.update_item(course, user_id)
    return course, course_data_path


def _import_static_content_wrapper(static_content_store, do_import_static, course_data_path, dest_course_id, verbose):
    # then import all the static content
    if static_content_store is not None and do_import_static:
        # first pass to find everything in /static/
        import_static_content(
            course_data_path, static_content_store,
            dest_course_id, subpath='static', verbose=verbose
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
        import_static_content(
            course_data_path, static_content_store,
            dest_course_id, subpath=simport, verbose=verbose
        )

def _import_module_and_update_references(
        module, store, user_id,
        source_course_id, dest_course_id,
        do_import_static=True, runtime=None):

    logging.debug(u'processing import of module {}...'.format(module.location.to_deprecated_string()))

    if do_import_static and 'data' in module.fields and isinstance(module.fields['data'], xblock.fields.String):
        # we want to convert all 'non-portable' links in the module_data
        # (if it is a string) to portable strings (e.g. /static/)
        module.data = rewrite_nonportable_content_links(
            source_course_id,
            dest_course_id,
            module.data
        )

    # Move the module to a new course
    def _convert_reference_fields_to_new_namespace(reference):
        """
        Convert a reference to the new namespace, but only
        if the original namespace matched the original course.

        Otherwise, returns the input value.
        """
        assert isinstance(reference, UsageKey)
        if source_course_id == reference.course_key:
            return reference.map_into_course(dest_course_id)
        else:
            return reference

    fields = {}
    for field_name, field in module.fields.iteritems():
        if field.is_set_on(module):
            if isinstance(field, Reference):
                fields[field_name] = _convert_reference_fields_to_new_namespace(field.read_from(module))
            elif isinstance(field, ReferenceList):
                references = field.read_from(module)
                fields[field_name] = [_convert_reference_fields_to_new_namespace(reference) for reference in references]
            elif isinstance(field, ReferenceValueDict):
                reference_dict = field.read_from(module)
                fields[field_name] = {
                    key: _convert_reference_fields_to_new_namespace(reference)
                    for key, reference
                    in reference_dict.items()
                }
            elif field_name == 'xml_attributes':
                value = field.read_from(module)
                # remove any export/import only xml_attributes
                # which are used to wire together draft imports
                if 'parent_sequential_url' in value:
                    del value['parent_sequential_url']

                if 'index_in_children_list' in value:
                    del value['index_in_children_list']
                fields[field_name] = value
            else:
                fields[field_name] = field.read_from(module)

    return store.import_xblock(user_id, dest_course_id, module.location.category, module.location.block_id, fields, runtime)


def _import_course_draft(
        xml_module_store,
        store,
        user_id,
        course_data_path,
        source_course_id,
        target_course_id,
        mongo_runtime
):
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
        course_id=source_course_id,
        course_dir=draft_course_dir,
        error_tracker=errorlog.tracker,
        parent_tracker=ParentTracker(),
        load_error_modules=False,
        mixins=xml_module_store.xblock_mixins,
        field_data=KvsFieldData(kvs=DictKeyValueStore()),
    )

    # now walk the /vertical directory where each file in there
    # will be a draft copy of the Vertical

    # First it is necessary to order the draft items by their desired index in the child list
    # (order os.walk returns them in is not guaranteed).
    drafts = dict()
    for dirname, _dirnames, filenames in os.walk(draft_dir + "/vertical"):
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

                    # process_xml call below recursively processes all descendants. If
                    # we call this on all verticals in a course with verticals nested below
                    # the unit level, we try to import the same content twice, causing naming conflicts.
                    # Therefore only process verticals at the unit level, assuming that any other
                    # verticals must be descendants.
                    if 'index_in_children_list' in xml:
                        descriptor = system.process_xml(xml)

                        # HACK: since we are doing partial imports of drafts
                        # the vertical doesn't have the 'url-name' set in the
                        # attributes (they are normally in the parent object,
                        # aka sequential), so we have to replace the location.name
                        # with the XML filename that is part of the pack
                        filename, __ = os.path.splitext(filename)
                        descriptor.location = descriptor.location.replace(name=filename)

                        index = int(descriptor.xml_attributes['index_in_children_list'])
                        if index in drafts:
                            drafts[index].append(descriptor)
                        else:
                            drafts[index] = [descriptor]

                except Exception:
                    logging.exception('Error while parsing course xml.')

        # For each index_in_children_list key, there is a list of vertical descriptors.
        for key in sorted(drafts.iterkeys()):
            for descriptor in drafts[key]:
                course_key = descriptor.location.course_key
                try:
                    def _import_module(module):
                        # IMPORTANT: Be sure to update the module location in the NEW namespace
                        module_location = module.location.map_into_course(target_course_id)
                        # Update the module's location to DRAFT revision
                        # We need to call this method (instead of updating the location directly)
                        # to ensure that pure XBlock field data is updated correctly.
                        _update_module_location(module, module_location.replace(revision=MongoRevisionKey.draft))

                        # make sure our parent has us in its list of children
                        # this is to make sure private only verticals show up
                        # in the list of children since they would have been
                        # filtered out from the non-draft store export.
                        # Note though that verticals nested below the unit level will not have
                        # a parent_sequential_url and do not need special handling.
                        if module.location.category == 'vertical' and 'parent_sequential_url' in module.xml_attributes:
                            sequential_url = module.xml_attributes['parent_sequential_url']
                            index = int(module.xml_attributes['index_in_children_list'])

                            seq_location = course_key.make_usage_key_from_deprecated_string(sequential_url)

                            # IMPORTANT: Be sure to update the sequential in the NEW namespace
                            seq_location = seq_location.map_into_course(target_course_id)
                            sequential = store.get_item(seq_location, depth=0)

                            non_draft_location = module.location.map_into_course(target_course_id)
                            if not any(child.block_id == module.location.block_id for child in sequential.children):
                                sequential.children.insert(index, non_draft_location)
                                store.update_item(sequential, user_id)

                        _import_module_and_update_references(
                            module, store, user_id,
                            source_course_id,
                            target_course_id,
                            runtime=mongo_runtime,
                        )
                        for child in module.get_children():
                            _import_module(child)

                    _import_module(descriptor)

                except Exception:
                    logging.exception('There while importing draft descriptor %s', descriptor)


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
                url=module.location.to_deprecated_string(), keys=illegal_keys
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
        for child_loc in parent.children:
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
    for err_log in module_store._course_errors.itervalues():
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
        if not module_store.has_item(course_id.make_usage_key('about', 'video')):
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


def _update_module_location(module, new_location):
    """
    Update a module's location.

    If the module is a pure XBlock (not an XModule), then its field data
    keys will need to be updated to include the new location.

    Args:
        module (XModuleMixin): The module to update.
        new_location (Location): The new location of the module.

    Returns:
        None

    """
    # Retrieve the content and settings fields that have been explicitly set
    # to ensure that they are properly re-keyed in the XBlock field data.
    if isinstance(module, XModuleDescriptor):
        rekey_fields = []
    else:
        rekey_fields = (
            module.get_explicitly_set_fields_by_scope(Scope.content).keys() +
            module.get_explicitly_set_fields_by_scope(Scope.settings).keys()
        )

    module.location = new_location

    # Pure XBlocks store the field data in a key-value store
    # in which one component of the key is the XBlock's location (equivalent to "scope_ids").
    # Since we've changed the XBlock's location, we need to re-save
    # all the XBlock's fields so they will be stored using the new location in the key.
    # However, since XBlocks only save "dirty" fields, we need to first
    # explicitly set each field to its current value before triggering the save.
    if len(rekey_fields) > 0:
        for rekey_field_name in rekey_fields:
            setattr(module, rekey_field_name, getattr(module, rekey_field_name))
        module.save()
