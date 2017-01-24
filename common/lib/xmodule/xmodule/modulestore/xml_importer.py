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
from abc import abstractmethod
from opaque_keys.edx.locator import LibraryLocator
import os
import mimetypes
from path import Path as path
import json
import re
from lxml import etree

from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore.xml import XMLModuleStore, LibraryXMLModuleStore, ImportSystem
from xblock.runtime import KvsFieldData, DictKeyValueStore
from xmodule.x_module import XModuleDescriptor, XModuleMixin
from opaque_keys.edx.keys import UsageKey
from xblock.fields import Scope, Reference, ReferenceList, ReferenceValueDict
from xmodule.contentstore.content import StaticContent
from .inheritance import own_metadata
from xmodule.errortracker import make_error_tracker
from .store_utilities import rewrite_nonportable_content_links
import xblock
from xmodule.tabs import CourseTabList
from xmodule.assetstore import AssetMetadata
from xmodule.modulestore.django import ASSET_IGNORE_REGEX
from xmodule.modulestore.exceptions import DuplicateCourseError
from xmodule.modulestore.mongo.base import MongoRevisionKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.store_utilities import draft_node_constructor, get_draft_subtree_roots
from xmodule.modulestore.tests.utils import LocationMixin
from xmodule.util.misc import escape_invalid_characters


log = logging.getLogger(__name__)


def import_static_content(
        course_data_path, static_content_store,
        target_id, subpath='static', verbose=False):

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
            asset_key = StaticContent.compute_location(target_id, fullname_with_subpath)

            policy_ele = policy.get(asset_key.path, {})

            # During export display name is used to create files, strip away slashes from name
            displayname = escape_invalid_characters(
                name=policy_ele.get('displayname', filename),
                invalid_char_list=['/', '\\']
            )
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


class ImportManager(object):
    """
    Import xml-based courselikes from data_dir into modulestore.

    Returns:
        list of new courselike objects

    Args:
        store: a modulestore implementing ModuleStoreWriteBase in which to store the imported courselikes.

        data_dir: the root directory from which to find the xml courselikes.

        source_dirs: If specified, the list of data_dir subdirectories to load. Otherwise, load
            all dirs

        target_id: is the Locator that all modules should be remapped to
            after import off disk. NOTE: this only makes sense if importing only
            one courselike. If there are more than one courselike loaded from data_dir/source_dirs & you
            supply this id, an AssertException will be raised.

        static_content_store: the static asset store

        do_import_static: if True, then import the courselike's static files into static_content_store
            This can be employed for courselikes which have substantial
            unchanging static content, which is too inefficient to import every
            time the course is loaded. Static content for some courses may also be
            served directly by nginx, instead of going through django.

        create_if_not_present: If True, then a new courselike is created if it doesn't already exist.
            Otherwise, it throws an InvalidLocationError if the courselike does not exist.

        default_class, load_error_modules: are arguments for constructing the XMLModuleStore (see its doc)
    """
    store_class = XMLModuleStore

    def __init__(
            self, store, user_id, data_dir, source_dirs=None,
            default_class='xmodule.raw_module.RawDescriptor',
            load_error_modules=True, static_content_store=None,
            target_id=None, verbose=False,
            do_import_static=True, create_if_not_present=False,
            raise_on_failure=False
    ):
        self.store = store
        self.user_id = user_id
        self.data_dir = data_dir
        self.source_dirs = source_dirs
        self.load_error_modules = load_error_modules
        self.static_content_store = static_content_store
        self.target_id = target_id
        self.verbose = verbose
        self.do_import_static = do_import_static
        self.create_if_not_present = create_if_not_present
        self.raise_on_failure = raise_on_failure
        self.xml_module_store = self.store_class(
            data_dir,
            default_class=default_class,
            source_dirs=source_dirs,
            load_error_modules=load_error_modules,
            xblock_mixins=store.xblock_mixins,
            xblock_select=store.xblock_select,
            target_course_id=target_id,
        )
        self.logger, self.errors = make_error_tracker()

    def preflight(self):
        """
        Perform any pre-import sanity checks.
        """
        # If we're going to remap the ID, then we can only do that with
        # a single target
        if self.target_id:
            assert len(self.xml_module_store.modules) == 1

    def import_static(self, data_path, dest_id):
        """
        Import all static items into the content store.
        """
        if self.static_content_store is not None and self.do_import_static:
            # first pass to find everything in /static/
            import_static_content(
                data_path, self.static_content_store,
                dest_id, subpath='static', verbose=self.verbose
            )

        elif self.verbose and not self.do_import_static:
            log.debug(
                "Skipping import of static content, "
                "since do_import_static=%s", self.do_import_static
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
        if os.path.exists(data_path / simport):
            import_static_content(
                data_path, self.static_content_store,
                dest_id, subpath=simport, verbose=self.verbose
            )

    def import_asset_metadata(self, data_dir, course_id):
        """
        Read in assets XML file, parse it, and add all asset metadata to the modulestore.
        """
        asset_dir = path(data_dir) / AssetMetadata.EXPORTED_ASSET_DIR
        assets_filename = AssetMetadata.EXPORTED_ASSET_FILENAME
        asset_xml_file = asset_dir / assets_filename

        def make_asset_id(course_id, asset_xml):
            """
            Construct an asset ID out of a complete asset XML section.
            """
            asset_type = None
            asset_name = None
            for child in asset_xml.iterchildren():
                if child.tag == AssetMetadata.ASSET_TYPE_ATTR:
                    asset_type = child.text
                elif child.tag == AssetMetadata.ASSET_BASENAME_ATTR:
                    asset_name = child.text
            return course_id.make_asset_key(asset_type, asset_name)

        all_assets = []
        try:
            xml_data = etree.parse(asset_xml_file).getroot()
            assert xml_data.tag == AssetMetadata.ALL_ASSETS_XML_TAG
            for asset in xml_data.iterchildren():
                if asset.tag == AssetMetadata.ASSET_XML_TAG:
                    # Construct the asset key.
                    asset_key = make_asset_id(course_id, asset)
                    asset_md = AssetMetadata(asset_key)
                    asset_md.from_xml(asset)
                    all_assets.append(asset_md)
        except IOError:
            logging.info('No %s file is present with asset metadata.', assets_filename)
            return
        except Exception:  # pylint: disable=W0703
            logging.exception('Error while parsing asset xml.')
            if self.raise_on_failure:
                raise
            else:
                return

        # Now add all asset metadata to the modulestore.
        if len(all_assets) > 0:
            self.store.save_asset_metadata_list(all_assets, all_assets[0].edited_by, import_only=True)

    def import_courselike(self, runtime, courselike_key, dest_id, source_courselike):
        """
        Import the base module/block
        """
        if self.verbose:
            log.debug("Scanning %s for courselike module...", courselike_key)

        # Quick scan to get course module as we need some info from there.
        # Also we need to make sure that the course module is committed
        # first into the store
        course_data_path = path(self.data_dir) / source_courselike.data_dir

        log.debug(u'======> IMPORTING courselike %s', courselike_key)

        if not self.do_import_static:
            # for old-style xblock where this was actually linked to kvs
            source_courselike.static_asset_path = source_courselike.data_dir
            source_courselike.save()
            log.debug('course static_asset_path=%s', source_courselike.static_asset_path)

        log.debug('course data_dir=%s', source_courselike.data_dir)

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, dest_id):
            course = _update_and_import_module(
                source_courselike, self.store, self.user_id,
                courselike_key,
                dest_id,
                do_import_static=self.do_import_static,
                runtime=runtime,
            )
            self.static_updater(course, source_courselike, courselike_key, dest_id, runtime)
            self.store.update_item(course, self.user_id)

        return course, course_data_path

    @abstractmethod
    def static_updater(self, course, source_courselike, courselike_key, dest_id, runtime):
        """
        Updates any special static items, such as PDF coursebooks.
        """
        pass

    @abstractmethod
    def get_dest_id(self, courselike_key):
        """
        Given a courselike_key, get the version of the key that will actually be used in the modulestore
        for import.
        """
        raise NotImplementedError

    @abstractmethod
    def get_courselike(self, courselike_key, runtime, dest_id):
        """
        Given a key, a runtime, and an intended destination key, get the descriptor for the courselike
        we'll be importing into.
        """
        raise NotImplementedError

    @abstractmethod
    def import_children(self, source_courselike, courselike, courselike_key, dest_id):
        """
        To be overloaded with a method that installs the child items into self.store.
        """
        raise NotImplementedError

    @abstractmethod
    def import_drafts(self, courselike, courselike_key, data_path, dest_id):
        """
        To be overloaded with a method that installs the draft items into self.store.
        """
        raise NotImplementedError

    def recursive_build(self, source_courselike, courselike, courselike_key, dest_id):
        """
        Recursively imports all child blocks from the temporary modulestore into the
        target modulestore.
        """
        all_locs = set(self.xml_module_store.modules[courselike_key].keys())
        all_locs.remove(source_courselike.location)

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
                    if self.verbose:
                        log.debug('importing module location %s', child.location)

                    _update_and_import_module(
                        child,
                        self.store,
                        self.user_id,
                        courselike_key,
                        dest_id,
                        do_import_static=self.do_import_static,
                        runtime=courselike.runtime,
                    )

                    depth_first(child)

        depth_first(source_courselike)

        for leftover in all_locs:
            if self.verbose:
                log.debug('importing module location %s', leftover)

            _update_and_import_module(
                self.xml_module_store.get_item(leftover),
                self.store,
                self.user_id,
                courselike_key,
                dest_id,
                do_import_static=self.do_import_static,
                runtime=courselike.runtime,
            )

    def run_imports(self):
        """
        Iterate over the given directories and yield courses.
        """
        self.preflight()
        for courselike_key in self.xml_module_store.modules.keys():
            try:
                dest_id, runtime = self.get_dest_id(courselike_key)
            except DuplicateCourseError:
                continue

            # This bulk operation wraps all the operations to populate the published branch.
            with self.store.bulk_operations(dest_id):
                # Retrieve the course itself.
                source_courselike, courselike, data_path = self.get_courselike(courselike_key, runtime, dest_id)

                # Import all static pieces.
                self.import_static(data_path, dest_id)

                # Import asset metadata stored in XML.
                self.import_asset_metadata(data_path, dest_id)

                # Import all children
                self.import_children(source_courselike, courselike, courselike_key, dest_id)

            # This bulk operation wraps all the operations to populate the draft branch with any items
            # from the /drafts subdirectory.
            # Drafts must be imported in a separate bulk operation from published items to import properly,
            # due to the recursive_build() above creating a draft item for each course block
            # and then publishing it.
            with self.store.bulk_operations(dest_id):
                # Import all draft items into the courselike.
                courselike = self.import_drafts(courselike, courselike_key, data_path, dest_id)

            yield courselike


class CourseImportManager(ImportManager):
    """
    Import manager for Courses.
    """
    store_class = XMLModuleStore

    def get_courselike(self, courselike_key, runtime, dest_id):
        """
        Given a key, runtime, and target key, get the version of the course
        from the temporary modulestore.
        """
        source_course = self.xml_module_store.get_course(courselike_key)
        # STEP 1: find and import course module
        course, course_data_path = self.import_courselike(
            runtime, courselike_key, dest_id, source_course,
        )
        return source_course, course, course_data_path

    def get_dest_id(self, courselike_key):
        """
        Get the course key that will be used for the target modulestore.
        """
        if self.target_id is not None:
            dest_id = self.target_id
        else:
            # Note that dest_course_id will be in the format for the default modulestore.
            dest_id = self.store.make_course_key(courselike_key.org, courselike_key.course, courselike_key.run)

        existing_id = self.store.has_course(dest_id, ignore_case=True)
        # store.has_course will return the course_key in the format for the modulestore in which it was found.
        # This may be different from dest_course_id, so correct to the format found.
        if existing_id:
            dest_id = existing_id

        runtime = None
        # Creates a new course if it doesn't already exist
        if self.create_if_not_present and not existing_id:
            try:
                new_course = self.store.create_course(
                    dest_id.org, dest_id.course, dest_id.run, self.user_id
                )
                runtime = new_course.runtime
            except DuplicateCourseError:
                log.debug(
                    "Skipping import of course with id, %s, "
                    "since it collides with an existing one", dest_id
                )
                raise

        return dest_id, runtime

    def static_updater(self, course, source_courselike, courselike_key, dest_id, runtime):
        """
        Update special static assets, such as PDF textbooks and wiki resources.
        """
        for entry in course.pdf_textbooks:
            for chapter in entry.get('chapters', []):
                if StaticContent.is_c4x_path(chapter.get('url', '')):
                    asset_key = StaticContent.get_location_from_path(chapter['url'])
                    chapter['url'] = StaticContent.get_static_path_from_location(asset_key)

        # Original wiki_slugs had value location.course. To make them unique this was changed to 'org.course.name'.
        # If we are importing into a course with a different course_id and wiki_slug is equal to either of these default
        # values then remap it so that the wiki does not point to the old wiki.
        if courselike_key != course.id:
            original_unique_wiki_slug = u'{0}.{1}.{2}'.format(
                courselike_key.org,
                courselike_key.course,
                courselike_key.run
            )
            if course.wiki_slug == original_unique_wiki_slug or course.wiki_slug == courselike_key.course:
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

    def import_children(self, source_courselike, courselike, courselike_key, dest_id):
        """
        Imports all children into the desired store.
        """
        # The branch setting of published_only forces an overwrite of all draft modules
        # during the course import.
        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only, dest_id):
            self.recursive_build(source_courselike, courselike, courselike_key, dest_id)

    def import_drafts(self, courselike, courselike_key, data_path, dest_id):
        """
        Imports all drafts into the desired store.
        """
        # Import any draft items
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, dest_id):
            _import_course_draft(
                self.xml_module_store,
                self.store,
                self.user_id,
                data_path,
                courselike_key,
                dest_id,
                courselike.runtime
            )

        # Importing the drafts potentially triggered a new structure version.
        # If so, the HEAD version_guid of the passed-in courselike will be out-of-date.
        # Fetch the course to return the most recent course version.
        return self.store.get_course(courselike.id.replace(branch=None, version_guid=None))


class LibraryImportManager(ImportManager):
    """
    Import manager for Libraries
    """
    store_class = LibraryXMLModuleStore

    def get_dest_id(self, courselike_key):
        """
        Get the LibraryLocator that will be used in the target modulestore.
        """
        if self.target_id is not None:
            dest_id = self.target_id
        else:
            dest_id = LibraryLocator(self.target_id.org, self.target_id.library)

        existing_lib = self.store.get_library(dest_id, ignore_case=True)

        runtime = None

        if existing_lib:
            dest_id = existing_lib.location.library_key
            runtime = existing_lib.runtime

        if self.create_if_not_present and not existing_lib:
            try:
                library = self.store.create_library(
                    org=self.target_id.org,
                    library=self.target_id.library,
                    user_id=self.user_id,
                    fields={"display_name": ""},
                )
                runtime = library.runtime
            except DuplicateCourseError:
                log.debug(
                    "Skipping import of Library with id %s, "
                    "since it collides with an existing one", dest_id
                )
                raise

        return dest_id, runtime

    def get_courselike(self, courselike_key, runtime, dest_id):
        """
        Get the descriptor of the library from the XML import modulestore.
        """
        source_library = self.xml_module_store.get_library(courselike_key)  # pylint: disable=no-member
        library, library_data_path = self.import_courselike(
            runtime, courselike_key, dest_id, source_library,
        )

        return source_library, library, library_data_path

    def static_updater(self, course, source_courselike, courselike_key, dest_id, runtime):
        """
        Libraries have no special static items to import.
        """
        pass

    def import_children(self, source_courselike, courselike, courselike_key, dest_id):
        """
        Imports all children into the desired store.
        """
        self.recursive_build(source_courselike, courselike, courselike_key, dest_id)

    def import_drafts(self, courselike, courselike_key, data_path, dest_id):
        """
        Imports all drafts into the desired store.
        """
        return courselike


def import_course_from_xml(*args, **kwargs):
    """
    Thin wrapper for the Course Import Manager. See ImportManager for details.
    """
    manager = CourseImportManager(*args, **kwargs)
    return list(manager.run_imports())


def import_library_from_xml(*args, **kwargs):
    """
    Thin wrapper for the Library Import Manager. See ImportManager for details.
    """
    manager = LibraryImportManager(*args, **kwargs)
    return list(manager.run_imports())


def _update_and_import_module(
        module, store, user_id,
        source_course_id, dest_course_id,
        do_import_static=True, runtime=None):
    """
    Update all the module reference fields to the destination course id,
    then import the module into the destination course.
    """
    logging.debug(u'processing import of module %s...', unicode(module.location))

    def _update_module_references(module, source_course_id, dest_course_id):
        """
        Move the module to a new course.
        """
        def _convert_ref_fields_to_new_namespace(reference):  # pylint: disable=invalid-name
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
            if field.scope != Scope.parent and field.is_set_on(module):
                if isinstance(field, Reference):
                    value = field.read_from(module)
                    if value is None:
                        fields[field_name] = None
                    else:
                        fields[field_name] = _convert_ref_fields_to_new_namespace(field.read_from(module))
                elif isinstance(field, ReferenceList):
                    references = field.read_from(module)
                    fields[field_name] = [_convert_ref_fields_to_new_namespace(reference) for reference in references]
                elif isinstance(field, ReferenceValueDict):
                    reference_dict = field.read_from(module)
                    fields[field_name] = {
                        key: _convert_ref_fields_to_new_namespace(reference)
                        for key, reference
                        in reference_dict.iteritems()
                    }
                elif field_name == 'xml_attributes':
                    value = field.read_from(module)
                    # remove any export/import only xml_attributes
                    # which are used to wire together draft imports
                    if 'parent_url' in value:
                        del value['parent_url']
                    if 'parent_sequential_url' in value:
                        del value['parent_sequential_url']

                    if 'index_in_children_list' in value:
                        del value['index_in_children_list']
                    fields[field_name] = value
                else:
                    fields[field_name] = field.read_from(module)
        return fields

    if do_import_static and 'data' in module.fields and isinstance(module.fields['data'], xblock.fields.String):
        # we want to convert all 'non-portable' links in the module_data
        # (if it is a string) to portable strings (e.g. /static/)
        module.data = rewrite_nonportable_content_links(
            source_course_id,
            dest_course_id,
            module.data
        )

    fields = _update_module_references(module, source_course_id, dest_course_id)
    asides = module.get_asides() if isinstance(module, XModuleMixin) else None

    block = store.import_xblock(
        user_id, dest_course_id, module.location.category,
        module.location.block_id, fields, runtime, asides=asides
    )

    # TODO: Move this code once the following condition is met.
    # Get to the point where XML import is happening inside the
    # modulestore that is eventually going to store the data.
    # Ticket: https://openedx.atlassian.net/browse/PLAT-1046
    if block.location.category == 'library_content':
        # if library exists, update source_library_version and children
        # according to this existing library and library content block.
        if store.get_library(block.source_library_key):

            # Update library content block's children on draft branch
            with store.branch_setting(branch_setting=ModuleStoreEnum.Branch.draft_preferred):
                LibraryToolsService(store).update_children(
                    block,
                    user_id,
                    version=block.source_library_version
                )

            # Publish it if importing the course for branch setting published_only.
            if store.get_branch_setting() == ModuleStoreEnum.Branch.published_only:
                store.publish(block.location, user_id)

    return block


def _import_course_draft(
        xml_module_store,
        store,
        user_id,
        course_data_path,
        source_course_id,
        target_id,
        mongo_runtime
):
    """
    This method will import all the content inside of the 'drafts' folder, if content exists.
    NOTE: This is not a full course import! In our current application, only verticals
    (and blocks beneath) can be in draft. Therefore, different call points into the import
    process_xml are used as the XMLModuleStore() constructor cannot simply be called
    (as is done for importing public content).
    """
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
    # Remove absolute path, leaving relative <course_name>/drafts.
    draft_course_dir = draft_dir.replace(data_dir, '', 1)

    system = ImportSystem(
        xmlstore=xml_module_store,
        course_id=source_course_id,
        course_dir=draft_course_dir,
        error_tracker=errorlog.tracker,
        load_error_modules=False,
        mixins=xml_module_store.xblock_mixins,
        field_data=KvsFieldData(kvs=DictKeyValueStore()),
        target_course_id=target_id,
    )

    def _import_module(module):
        # IMPORTANT: Be sure to update the module location in the NEW namespace
        module_location = module.location.map_into_course(target_id)
        # Update the module's location to DRAFT revision
        # We need to call this method (instead of updating the location directly)
        # to ensure that pure XBlock field data is updated correctly.
        _update_module_location(module, module_location.replace(revision=MongoRevisionKey.draft))

        parent_url = get_parent_url(module)
        index = index_in_children_list(module)

        # make sure our parent has us in its list of children
        # this is to make sure private only modules show up
        # in the list of children since they would have been
        # filtered out from the non-draft store export.
        if parent_url is not None and index is not None:
            course_key = descriptor.location.course_key
            parent_location = course_key.make_usage_key_from_deprecated_string(parent_url)

            # IMPORTANT: Be sure to update the parent in the NEW namespace
            parent_location = parent_location.map_into_course(target_id)

            parent = store.get_item(parent_location, depth=0)

            non_draft_location = module.location.map_into_course(target_id)
            if not any(child.block_id == module.location.block_id for child in parent.children):
                parent.children.insert(index, non_draft_location)
                store.update_item(parent, user_id)

        _update_and_import_module(
            module, store, user_id,
            source_course_id,
            target_id,
            runtime=mongo_runtime,
        )
        for child in module.get_children():
            _import_module(child)

    # Now walk the /drafts directory.
    # Each file in the directory will be a draft copy of the vertical.

    # First it is necessary to order the draft items by their desired index in the child list,
    # since the order in which os.walk() returns the files is not guaranteed.
    drafts = []
    for rootdir, __, filenames in os.walk(draft_dir):
        for filename in filenames:
            if filename.startswith('._'):
                # Skip any OSX quarantine files, prefixed with a '._'.
                continue
            module_path = os.path.join(rootdir, filename)
            with open(module_path, 'r') as f:
                try:
                    xml = f.read().decode('utf-8')

                    # The process_xml() call below recursively processes all descendants. If
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

                        index = index_in_children_list(descriptor)
                        parent_url = get_parent_url(descriptor, xml)
                        draft_url = unicode(descriptor.location)

                        draft = draft_node_constructor(
                            module=descriptor, url=draft_url, parent_url=parent_url, index=index
                        )
                        drafts.append(draft)

                except Exception:  # pylint: disable=broad-except
                    logging.exception('Error while parsing course drafts xml.')

    # Sort drafts by `index_in_children_list` attribute.
    drafts.sort(key=lambda x: x.index)

    for draft in get_draft_subtree_roots(drafts):
        try:
            _import_module(draft.module)
        except Exception:  # pylint: disable=broad-except
            logging.exception('while importing draft descriptor %s', draft.module)


def allowed_metadata_by_category(category):
    # should this be in the descriptors?!?
    return {
        'vertical': [],
        'chapter': ['start'],
        'sequential': ['due', 'format', 'start', 'graded']
    }.get(category, ['*'])


def check_module_metadata_editability(module):
    """
    Assert that there is no metadata within a particular module that
    we can't support editing. However we always allow 'display_name'
    and 'xml_attributes'
    """
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
                url=unicode(module.location), keys=illegal_keys
            )
        )

    return err_cnt


def get_parent_url(module, xml=None):
    """
    Get the parent_url, if any, from module using xml as an alternative source. If it finds it in
    xml but not on module, it modifies module so that the next call to this w/o the xml will get the parent url
    """
    if hasattr(module, 'xml_attributes'):
        return module.xml_attributes.get(
            # handle deprecated old attr
            'parent_url', module.xml_attributes.get('parent_sequential_url')
        )
    if xml is not None:
        create_xml_attributes(module, xml)
        return get_parent_url(module)  # don't reparse xml b/c don't infinite recurse but retry above lines
    return None


def index_in_children_list(module, xml=None):
    """
    Get the index_in_children_list, if any, from module using xml
    as an alternative source. If it finds it in xml but not on module,
    it modifies module so that the next call to this w/o the xml
    will get the field.
    """
    if hasattr(module, 'xml_attributes'):
        val = module.xml_attributes.get('index_in_children_list')
        if val is not None:
            return int(val)
        return None
    if xml is not None:
        create_xml_attributes(module, xml)
        return index_in_children_list(module)  # don't reparse xml b/c don't infinite recurse but retry above lines
    return None


def create_xml_attributes(module, xml):
    """
    Make up for modules which don't define xml_attributes by creating them here and populating
    """
    xml_attrs = {}
    for attr, val in xml.attrib.iteritems():
        if attr not in module.fields:
            # translate obsolete attr
            if attr == 'parent_sequential_url':
                attr = 'parent_url'
            xml_attrs[attr] = val

    # now cache it on module where it's expected
    module.xml_attributes = xml_attrs


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
        data_dir, source_dirs,
        default_class='xmodule.raw_module.RawDescriptor',
        load_error_modules=True,
        xblock_mixins=(LocationMixin, XModuleMixin)):
    err_cnt = 0
    warn_cnt = 0

    module_store = XMLModuleStore(
        data_dir,
        default_class=default_class,
        source_dirs=source_dirs,
        load_error_modules=load_error_modules,
        xblock_mixins=xblock_mixins
    )

    # check all data source path information
    for course_dir in source_dirs:
        _err_cnt, _warn_cnt = validate_data_source_paths(path(data_dir), course_dir)
        err_cnt += _err_cnt
        warn_cnt += _warn_cnt

    # first count all errors and warnings as part of the XMLModuleStore import
    for err_log in module_store._course_errors.itervalues():  # pylint: disable=protected-access
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

    print "\n"
    print "------------------------------------------"
    print "VALIDATION SUMMARY: {err} Errors   {warn} Warnings".format(
        err=err_cnt,
        warn=warn_cnt
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
        print "This course can be imported successfully."

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
            module.get_explicitly_set_fields_by_scope(Scope.settings).keys() +
            module.get_explicitly_set_fields_by_scope(Scope.children).keys()
        )

    module.location = new_location

    # Pure XBlocks store the field data in a key-value store
    # in which one component of the key is the XBlock's location (equivalent to "scope_ids").
    # Since we've changed the XBlock's location, we need to re-save
    # all the XBlock's fields so they will be stored using the new location in the key.
    # However, since XBlocks only save "dirty" fields, we need to call
    # XBlock's `force_save_fields_method`
    if len(rekey_fields) > 0:
        module.force_save_fields(rekey_fields)
