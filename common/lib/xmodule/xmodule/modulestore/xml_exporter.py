"""
Methods for exporting course data to XML
"""

import logging
from abc import abstractmethod
import lxml.etree
from xblock.fields import Scope, Reference, ReferenceList, ReferenceValueDict
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from xmodule.assetstore import AssetMetadata
from xmodule.modulestore import EdxJSONEncoder, ModuleStoreEnum
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.store_utilities import draft_node_constructor, get_draft_subtree_roots
from xmodule.modulestore import LIBRARY_ROOT
from fs.osfs import OSFS
from json import dumps
import json
import os
from path import Path as path
import shutil
from xmodule.modulestore.draft_and_published import DIRECT_ONLY_CATEGORIES
from opaque_keys.edx.locator import CourseLocator, LibraryLocator

DRAFT_DIR = "drafts"
PUBLISHED_DIR = "published"
EXPORT_VERSION_FILE = "format.json"
EXPORT_VERSION_KEY = "export_format"

DEFAULT_CONTENT_FIELDS = ['metadata', 'data']


def _export_drafts(modulestore, course_key, export_fs, xml_centric_course_key):
    """
    Exports course drafts.
    """
    # NOTE: we need to explicitly implement the logic for setting the vertical's parent
    # and index here since the XML modulestore cannot load draft modules
    with modulestore.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course_key):
        draft_modules = modulestore.get_items(
            course_key,
            qualifiers={'category': {'$nin': DIRECT_ONLY_CATEGORIES}},
            revision=ModuleStoreEnum.RevisionOption.draft_only
        )
        # Check to see if the returned draft modules have changes w.r.t. the published module.
        # Only modules with changes will be exported into the /drafts directory.
        draft_modules = [module for module in draft_modules if modulestore.has_changes(module)]

        if draft_modules:
            draft_course_dir = export_fs.makeopendir(DRAFT_DIR)

            # accumulate tuples of draft_modules and their parents in
            # this list:
            draft_node_list = []

            for draft_module in draft_modules:
                parent_loc = modulestore.get_parent_location(
                    draft_module.location,
                    revision=ModuleStoreEnum.RevisionOption.draft_preferred
                )

                # if module has no parent, set its parent_url to `None`
                parent_url = None
                if parent_loc is not None:
                    parent_url = parent_loc.to_deprecated_string()

                draft_node = draft_node_constructor(
                    draft_module,
                    location=draft_module.location,
                    url=draft_module.location.to_deprecated_string(),
                    parent_location=parent_loc,
                    parent_url=parent_url,
                )

                draft_node_list.append(draft_node)

            for draft_node in get_draft_subtree_roots(draft_node_list):
                # only export the roots of the draft subtrees
                # since export_from_xml (called by `add_xml_to_node`)
                # exports a whole tree

                # ensure module has "xml_attributes" attr
                if not hasattr(draft_node.module, 'xml_attributes'):
                    draft_node.module.xml_attributes = {}

                # Don't try to export orphaned items
                # and their descendents
                if draft_node.parent_location is None:
                    continue

                logging.debug('parent_loc = %s', draft_node.parent_location)

                draft_node.module.xml_attributes['parent_url'] = draft_node.parent_url
                parent = modulestore.get_item(draft_node.parent_location)
                index = parent.children.index(draft_node.module.location)
                draft_node.module.xml_attributes['index_in_children_list'] = str(index)

                draft_node.module.runtime.export_fs = draft_course_dir
                adapt_references(draft_node.module, xml_centric_course_key, draft_course_dir)
                node = lxml.etree.Element('unknown')

                draft_node.module.add_xml_to_node(node)


class ExportManager(object):
    """
    Manages XML exporting for courselike objects.
    """
    def __init__(self, modulestore, contentstore, courselike_key, root_dir, target_dir):
        """
        Export all modules from `modulestore` and content from `contentstore` as xml to `root_dir`.

        `modulestore`: A `ModuleStore` object that is the source of the modules to export
        `contentstore`: A `ContentStore` object that is the source of the content to export, can be None
        `courselike_key`: The Locator of the Descriptor to export
        `root_dir`: The directory to write the exported xml to
        `target_dir`: The name of the directory inside `root_dir` to write the content to
        """
        self.modulestore = modulestore
        self.contentstore = contentstore
        self.courselike_key = courselike_key
        self.root_dir = root_dir
        self.target_dir = target_dir

    @abstractmethod
    def get_key(self):
        """
        Get the courselike locator key
        """
        raise NotImplementedError

    def process_root(self, root, export_fs):
        """
        Perform any additional tasks to the root XML node.
        """

    def process_extra(self, root, courselike, root_courselike_dir, xml_centric_courselike_key, export_fs):
        """
        Process additional content, like static assets.
        """

    def post_process(self, root, export_fs):
        """
        Perform any final processing after the other export tasks are done.
        """

    @abstractmethod
    def get_courselike(self):
        """
        Get the target courselike object for this export.
        """

    def export(self):
        """
        Perform the export given the parameters handed to this class at init.
        """
        with self.modulestore.bulk_operations(self.courselike_key):

            fsm = OSFS(self.root_dir)
            root = lxml.etree.Element('unknown')

            # export only the published content
            with self.modulestore.branch_setting(ModuleStoreEnum.Branch.published_only, self.courselike_key):
                courselike = self.get_courselike()
                export_fs = courselike.runtime.export_fs = fsm.makeopendir(self.target_dir)

                # change all of the references inside the course to use the xml expected key type w/o version & branch
                xml_centric_courselike_key = self.get_key()
                adapt_references(courselike, xml_centric_courselike_key, export_fs)
                courselike.add_xml_to_node(root)

            # Make any needed adjustments to the root node.
            self.process_root(root, export_fs)

            # Process extra items-- drafts, assets, etc
            root_courselike_dir = self.root_dir + '/' + self.target_dir
            self.process_extra(root, courselike, root_courselike_dir, xml_centric_courselike_key, export_fs)

            # Any last pass adjustments
            self.post_process(root, export_fs)


class CourseExportManager(ExportManager):
    """
    Export manager for courses.
    """
    def get_key(self):
        return CourseLocator(
            self.courselike_key.org, self.courselike_key.course, self.courselike_key.run, deprecated=True
        )

    def get_courselike(self):
        # depth = None: Traverses down the entire course structure.
        # lazy = False: Loads and caches all block definitions during traversal for fast access later
        #               -and- to eliminate many round-trips to read individual definitions.
        # Why these parameters? Because a course export needs to access all the course block information
        # eventually. Accessing it all now at the beginning increases performance of the export.
        return self.modulestore.get_course(self.courselike_key, depth=None, lazy=False)

    def process_root(self, root, export_fs):
        with export_fs.open('course.xml', 'w') as course_xml:
            lxml.etree.ElementTree(root).write(course_xml)

    def process_extra(self, root, courselike, root_courselike_dir, xml_centric_courselike_key, export_fs):
        # Export the modulestore's asset metadata.
        asset_dir = root_courselike_dir + '/' + AssetMetadata.EXPORTED_ASSET_DIR + '/'
        if not os.path.isdir(asset_dir):
            os.makedirs(asset_dir)
        asset_root = lxml.etree.Element(AssetMetadata.ALL_ASSETS_XML_TAG)
        course_assets = self.modulestore.get_all_asset_metadata(self.courselike_key, None)
        for asset_md in course_assets:
            # All asset types are exported using the "asset" tag - but their asset type is specified in each asset key.
            asset = lxml.etree.SubElement(asset_root, AssetMetadata.ASSET_XML_TAG)
            asset_md.to_xml(asset)
        with OSFS(asset_dir).open(AssetMetadata.EXPORTED_ASSET_FILENAME, 'w') as asset_xml_file:
            lxml.etree.ElementTree(asset_root).write(asset_xml_file)

        # export the static assets
        policies_dir = export_fs.makeopendir('policies')
        if self.contentstore:
            self.contentstore.export_all_for_course(
                self.courselike_key,
                root_courselike_dir + '/static/',
                root_courselike_dir + '/policies/assets.json',
            )

            # If we are using the default course image, export it to the
            # legacy location to support backwards compatibility.
            if courselike.course_image == courselike.fields['course_image'].default:
                try:
                    course_image = self.contentstore.find(
                        StaticContent.compute_location(
                            courselike.id,
                            courselike.course_image
                        ),
                    )
                except NotFoundError:
                    pass
                else:
                    output_dir = root_courselike_dir + '/static/images/'
                    if not os.path.isdir(output_dir):
                        os.makedirs(output_dir)
                    with OSFS(output_dir).open('course_image.jpg', 'wb') as course_image_file:
                        course_image_file.write(course_image.data)

        # export the static tabs
        export_extra_content(
            export_fs, self.modulestore, self.courselike_key, xml_centric_courselike_key,
            'static_tab', 'tabs', '.html'
        )

        # export the custom tags
        export_extra_content(
            export_fs, self.modulestore, self.courselike_key, xml_centric_courselike_key,
            'custom_tag_template', 'custom_tags'
        )

        # export the course updates
        export_extra_content(
            export_fs, self.modulestore, self.courselike_key, xml_centric_courselike_key,
            'course_info', 'info', '.html'
        )

        # export the 'about' data (e.g. overview, etc.)
        export_extra_content(
            export_fs, self.modulestore, self.courselike_key, xml_centric_courselike_key,
            'about', 'about', '.html'
        )

        course_policy_dir_name = courselike.location.run
        if courselike.url_name != courselike.location.run and courselike.url_name == 'course':
            # Use url_name for split mongo because course_run is not used when loading policies.
            course_policy_dir_name = courselike.url_name

        course_run_policy_dir = policies_dir.makeopendir(course_policy_dir_name)

        # export the grading policy
        with course_run_policy_dir.open('grading_policy.json', 'w') as grading_policy:
            grading_policy.write(dumps(courselike.grading_policy, cls=EdxJSONEncoder, sort_keys=True, indent=4))

        # export all of the course metadata in policy.json
        with course_run_policy_dir.open('policy.json', 'w') as course_policy:
            policy = {'course/' + courselike.location.name: own_metadata(courselike)}
            course_policy.write(dumps(policy, cls=EdxJSONEncoder, sort_keys=True, indent=4))

        # xml backed courses don't support drafts!
        if courselike.runtime.modulestore.get_modulestore_type() != ModuleStoreEnum.Type.xml:
            _export_drafts(self.modulestore, self.courselike_key, export_fs, xml_centric_courselike_key)


class LibraryExportManager(ExportManager):
    """
    Export manager for Libraries
    """
    def get_key(self):
        """
        Get the library locator for the current library key.
        """
        return LibraryLocator(
            self.courselike_key.org, self.courselike_key.library
        )

    def get_courselike(self):
        """
        Get the library from the modulestore.
        """
        return self.modulestore.get_library(self.courselike_key, depth=None, lazy=False)

    def process_root(self, root, export_fs):
        """
        Add extra attributes to the root XML file.
        """
        root.set('org', self.courselike_key.org)
        root.set('library', self.courselike_key.library)

    def process_extra(self, root, courselike, root_courselike_dir, xml_centric_courselike_key, export_fs):
        """
        Notionally, libraries may have assets. This is currently unsupported, but the structure is here
        to ease in duck typing during import. This may be expanded as a useful feature eventually.
        """
        # export the static assets
        export_fs.makeopendir('policies')

        if self.contentstore:
            self.contentstore.export_all_for_course(
                self.courselike_key,
                self.root_dir + '/' + self.target_dir + '/static/',
                self.root_dir + '/' + self.target_dir + '/policies/assets.json',
            )

    def post_process(self, root, export_fs):
        """
        Because Libraries are XBlocks, they aren't exported in the same way Course Modules
        are, but instead use the standard XBlock serializers. Accordingly, we need to
        create our own index file to act as the equivalent to the root course.xml file,
        called library.xml.
        """
        # Create the Library.xml file, which acts as the index of all library contents.
        xml_file = export_fs.open(LIBRARY_ROOT, 'w')
        xml_file.write(lxml.etree.tostring(root, pretty_print=True, encoding='utf-8'))
        xml_file.close()


def export_course_to_xml(modulestore, contentstore, course_key, root_dir, course_dir):
    """
    Thin wrapper for the Course Export Manager. See ExportManager for details.
    """
    CourseExportManager(modulestore, contentstore, course_key, root_dir, course_dir).export()


def export_library_to_xml(modulestore, contentstore, library_key, root_dir, library_dir):
    """
    Thin wrapper for the Library Export Manager. See ExportManager for details.
    """
    LibraryExportManager(modulestore, contentstore, library_key, root_dir, library_dir).export()


def adapt_references(subtree, destination_course_key, export_fs):
    """
    Map every reference in the subtree into destination_course_key and set it back into the xblock fields
    """
    subtree.runtime.export_fs = export_fs  # ensure everything knows where it's going!
    for field_name, field in subtree.fields.iteritems():
        if field.is_set_on(subtree):
            if isinstance(field, Reference):
                value = field.read_from(subtree)
                if value is not None:
                    field.write_to(subtree, field.read_from(subtree).map_into_course(destination_course_key))
            elif field_name == 'children':
                # don't change the children field but do recurse over the children
                [adapt_references(child, destination_course_key, export_fs) for child in subtree.get_children()]
            elif isinstance(field, ReferenceList):
                field.write_to(
                    subtree,
                    [ele.map_into_course(destination_course_key) for ele in field.read_from(subtree)]
                )
            elif isinstance(field, ReferenceValueDict):
                field.write_to(
                    subtree, {
                        key: ele.map_into_course(destination_course_key) for key, ele in field.read_from(subtree).iteritems()
                    }
                )


def _export_field_content(xblock_item, item_dir):
    """
    Export all fields related to 'xblock_item' other than 'metadata' and 'data' to json file in provided directory
    """
    module_data = xblock_item.get_explicitly_set_fields_by_scope(Scope.content)
    if isinstance(module_data, dict):
        for field_name in module_data:
            if field_name not in DEFAULT_CONTENT_FIELDS:
                # filename format: {dirname}.{field_name}.json
                with item_dir.open('{0}.{1}.{2}'.format(xblock_item.location.name, field_name, 'json'),
                                   'w') as field_content_file:
                    field_content_file.write(dumps(module_data.get(field_name, {}), cls=EdxJSONEncoder, sort_keys=True, indent=4))


def export_extra_content(export_fs, modulestore, source_course_key, dest_course_key, category_type, dirname, file_suffix=''):
    items = modulestore.get_items(source_course_key, qualifiers={'category': category_type})

    if len(items) > 0:
        item_dir = export_fs.makeopendir(dirname)
        for item in items:
            adapt_references(item, dest_course_key, export_fs)
            with item_dir.open(item.location.name + file_suffix, 'w') as item_file:
                item_file.write(item.data.encode('utf8'))

                # export content fields other then metadata and data in json format in current directory
                _export_field_content(item, item_dir)


def convert_between_versions(source_dir, target_dir):
    """
    Converts a version 0 export format to version 1, and vice versa.

    @param source_dir: the directory structure with the course export that should be converted.
       The contents of source_dir will not be altered.
    @param target_dir: the directory where the converted export should be written.
    @return: the version number of the converted export.
    """
    def convert_to_version_1():
        """ Convert a version 0 archive to version 0 """
        os.mkdir(copy_root)
        with open(copy_root / EXPORT_VERSION_FILE, 'w') as f:
            f.write('{{"{export_key}": 1}}\n'.format(export_key=EXPORT_VERSION_KEY))

        # If a drafts folder exists, copy it over.
        copy_drafts()

        # Now copy everything into the published directory
        published_dir = copy_root / PUBLISHED_DIR
        shutil.copytree(path(source_dir) / course_name, published_dir)
        # And delete the nested drafts directory, if it exists.
        nested_drafts_dir = published_dir / DRAFT_DIR
        if nested_drafts_dir.isdir():
            shutil.rmtree(nested_drafts_dir)

    def convert_to_version_0():
        """ Convert a version 1 archive to version 0 """
        # Copy everything in "published" up to the top level.
        published_dir = path(source_dir) / course_name / PUBLISHED_DIR
        if not published_dir.isdir():
            raise ValueError("a version 1 archive must contain a published branch")

        shutil.copytree(published_dir, copy_root)

        # If there is a DRAFT branch, copy it. All other branches are ignored.
        copy_drafts()

    def copy_drafts():
        """
        Copy drafts directory from the old archive structure to the new.
        """
        draft_dir = path(source_dir) / course_name / DRAFT_DIR
        if draft_dir.isdir():
            shutil.copytree(draft_dir, copy_root / DRAFT_DIR)

    root = os.listdir(source_dir)
    if len(root) != 1 or (path(source_dir) / root[0]).isfile():
        raise ValueError("source archive does not have single course directory at top level")

    course_name = root[0]

    # For this version of the script, we simply convert back and forth between version 0 and 1.
    original_version = get_version(path(source_dir) / course_name)
    if original_version not in [0, 1]:
        raise ValueError("unknown version: " + str(original_version))
    desired_version = 1 if original_version is 0 else 0

    copy_root = path(target_dir) / course_name

    if desired_version == 1:
        convert_to_version_1()
    else:
        convert_to_version_0()

    return desired_version


def get_version(course_path):
    """
    Return the export format version number for the given
    archive directory structure (represented as a path instance).

    If the archived file does not correspond to a known export
    format, None will be returned.
    """
    format_file = course_path / EXPORT_VERSION_FILE
    if not format_file.isfile():
        return 0
    with open(format_file, "r") as f:
        data = json.load(f)
        if EXPORT_VERSION_KEY in data:
            return data[EXPORT_VERSION_KEY]

    return None
