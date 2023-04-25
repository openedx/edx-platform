"""
Modulestore backed by Mongodb.

Stores individual XModules as single documents with the following
structure:

{
    '_id': <location.as_dict>,
    'metadata': <dict containing all Scope.settings fields>
    'definition': <dict containing all Scope.content fields>
    'definition.children': <list of all child text_type(location)s>
}
"""


import copy
import logging
import re
import sys
from datetime import datetime
from importlib import import_module
from uuid import uuid4

import pymongo
from bson.son import SON
from fs.osfs import OSFS
from mongodb_proxy import autoretry_read
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator, LibraryLocator
from path import Path as path
from pytz import UTC
from xblock.core import XBlock
from xblock.exceptions import InvalidScopeError
from xblock.fields import Reference, ReferenceList, ReferenceValueDict, Scope, ScopeIds
from xblock.runtime import KvsFieldData

from xmodule.assetstore import AssetMetadata, CourseAssetsFromStorage
from xmodule.course_block import CourseSummary
from xmodule.error_block import ErrorBlock
from xmodule.errortracker import exc_info_to_str, null_error_tracker
from xmodule.exceptions import HeartbeatFailure
from xmodule.mako_block import MakoDescriptorSystem
from xmodule.modulestore import BulkOperationsMixin, ModuleStoreEnum, ModuleStoreWriteBase
from xmodule.modulestore.draft_and_published import DIRECT_ONLY_CATEGORIES, ModuleStoreDraftAndPublished
from xmodule.modulestore.edit_info import EditInfoRuntimeMixin
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError, ReferentialIntegrityError
from xmodule.modulestore.inheritance import InheritanceKeyValueStore, InheritanceMixin, inherit_metadata
from xmodule.modulestore.store_utilities import DETACHED_XBLOCK_TYPES
from xmodule.modulestore.xml import CourseLocationManager
from xmodule.mongo_utils import connect_to_mongodb, create_collection_index
from xmodule.partitions.partitions_service import PartitionService
from xmodule.services import SettingsService

log = logging.getLogger(__name__)

# sort order that returns DRAFT items first
SORT_REVISION_FAVOR_DRAFT = ('_id.revision', pymongo.DESCENDING)

# sort order that returns PUBLISHED items first
SORT_REVISION_FAVOR_PUBLISHED = ('_id.revision', pymongo.ASCENDING)

BLOCK_TYPES_WITH_CHILDREN = list({
    name for name, class_ in XBlock.load_classes() if getattr(class_, 'has_children', False)
})

# Allow us to call _from_deprecated_(son|string) throughout the file
# pylint: disable=protected-access

# at module level, cache one instance of OSFS per filesystem root.
_OSFS_INSTANCE = {}


class MongoRevisionKey:
    """
    Key Revision constants to use for Location and Usage Keys in the Mongo modulestore
    Note: These values are persisted in the database, so should not be changed without migrations
    """
    draft = 'draft'
    published = None


class InvalidWriteError(Exception):
    """
    Raised to indicate that writing to a particular key
    in the KeyValueStore is disabled
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class MongoKeyValueStore(InheritanceKeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """
    def __init__(self, data, parent, children, metadata):
        super().__init__()
        if not isinstance(data, dict):
            self._data = {'data': data}
        else:
            self._data = data
        self._parent = parent
        self._children = children
        self._metadata = metadata

    def get(self, key):
        if key.scope == Scope.children:
            return self._children
        elif key.scope == Scope.parent:
            return self._parent
        elif key.scope == Scope.settings:
            return self._metadata[key.field_name]
        elif key.scope == Scope.content:
            return self._data[key.field_name]
        else:
            raise InvalidScopeError(
                key,
                (Scope.children, Scope.parent, Scope.settings, Scope.content),
            )

    def set(self, key, value):
        if key.scope == Scope.children:
            self._children = value
        elif key.scope == Scope.parent:
            self._parent = value
        elif key.scope == Scope.settings:
            self._metadata[key.field_name] = value
        elif key.scope == Scope.content:
            self._data[key.field_name] = value
        else:
            raise InvalidScopeError(
                key,
                (Scope.children, Scope.settings, Scope.content),
            )

    def delete(self, key):
        if key.scope == Scope.children:
            self._children = []
        elif key.scope == Scope.settings:
            if key.field_name in self._metadata:
                del self._metadata[key.field_name]
        elif key.scope == Scope.content:
            if key.field_name in self._data:
                del self._data[key.field_name]
        else:
            raise InvalidScopeError(
                key,
                (Scope.children, Scope.settings, Scope.content),
            )

    def has(self, key):
        if key.scope in (Scope.children, Scope.parent):
            return True
        elif key.scope == Scope.settings:
            return key.field_name in self._metadata
        elif key.scope == Scope.content:
            return key.field_name in self._data
        else:
            return False

    def __repr__(self):
        return "MongoKeyValueStore{!r}<{!r}, {!r}>".format(
            (self._data, self._parent, self._children, self._metadata),
            self._fields,
            self.inherited_settings
        )


class CachingDescriptorSystem(MakoDescriptorSystem, EditInfoRuntimeMixin):  # lint-amnesty, pylint: disable=abstract-method
    """
    A system that has a cache of block json that it will use to load blocks
    from, with a backup of calling to the underlying modulestore for more data
    """
    def __repr__(self):
        return "CachingDescriptorSystem{!r}".format((
            self.modulestore,
            str(self.course_id),
            [str(key) for key in self.module_data.keys()],
            self.default_class,
        ))

    def __init__(self, modulestore, course_key, module_data, default_class, **kwargs):
        """
        modulestore: the module store that can be used to retrieve additional blocks

        course_key: the course for which everything in this runtime will be relative

        module_data: a dict mapping Location -> json that was cached from the
            underlying modulestore

        default_class: The default_class to use when loading an
            XModuleDescriptor from the module_data

        resources_fs: a filesystem, as per MakoDescriptorSystem

        error_tracker: a function that logs errors for later display to users

        render_template: a function for rendering templates, as per
            MakoDescriptorSystem
        """
        id_manager = CourseLocationManager(course_key)
        kwargs.setdefault('id_reader', id_manager)
        kwargs.setdefault('id_generator', id_manager)
        super().__init__(
            load_item=self.load_item,
            **kwargs
        )

        self.modulestore = modulestore
        self.module_data = module_data
        self.default_class = default_class
        # cdodge: other Systems have a course_id attribute defined. To keep things consistent, let's
        # define an attribute here as well, even though it's None
        self.course_id = course_key

    def load_item(self, location, for_parent=None):  # lint-amnesty, pylint: disable=method-hidden
        """
        Return an XBlock instance for the specified location
        """
        assert isinstance(location, UsageKey)

        if location.run is None:
            # self.module_data is keyed on locations that have full run information.
            # If the supplied location is missing a run, then we will miss the cache and
            # incur an additional query.
            # TODO: make module_data a proper class that can handle this itself.
            location = location.replace(course_key=self.modulestore.fill_in_run(location.course_key))

        json_data = self.module_data.get(location)
        if json_data is None:
            block = self.modulestore.get_item(location, using_descriptor_system=self)
            return block
        else:
            # load the block and apply the inherited metadata
            try:
                category = json_data['location']['category']
                class_ = self.load_block_type(category)

                definition = json_data.get('definition', {})
                metadata = json_data.get('metadata', {})

                children = [
                    self._convert_reference_to_key(childloc)
                    for childloc in definition.get('children', [])
                ]

                parent = None
                if category not in DETACHED_XBLOCK_TYPES.union(['course']):
                    # try looking it up just-in-time (but not if we're working with a detached block).
                    parent = self.modulestore.get_parent_location(
                        as_published(location),
                        ModuleStoreEnum.RevisionOption.published_only if location.branch is None
                        else ModuleStoreEnum.RevisionOption.draft_preferred
                    )

                data = definition.get('data', {})
                if isinstance(data, str):
                    data = {'data': data}

                mixed_class = self.mixologist.mix(class_)
                if data:  # empty or None means no work
                    data = self._convert_reference_fields_to_keys(mixed_class, location.course_key, data)
                metadata = self._convert_reference_fields_to_keys(mixed_class, location.course_key, metadata)
                kvs = MongoKeyValueStore(
                    data,
                    parent,
                    children,
                    metadata,
                )

                field_data = KvsFieldData(kvs)
                scope_ids = ScopeIds(None, category, location, location)
                block = self.construct_xblock_from_class(class_, scope_ids, field_data, for_parent=for_parent)

                non_draft_loc = as_published(location)
                metadata_inheritance_tree = self.modulestore._compute_metadata_inheritance_tree(self.course_id)
                inherit_metadata(block, metadata_inheritance_tree.get(str(non_draft_loc), {}))

                block._edit_info = json_data.get('edit_info')

                # migrate published_by and published_on if edit_info isn't present
                if block._edit_info is None:
                    block._edit_info = {}
                    raw_metadata = json_data.get('metadata', {})
                    # published_on was previously stored as a list of time components instead of a datetime
                    if raw_metadata.get('published_date'):
                        block._edit_info['published_date'] = datetime(
                            *raw_metadata.get('published_date')[0:6]
                        ).replace(tzinfo=UTC)
                    block._edit_info['published_by'] = raw_metadata.get('published_by')

                for wrapper in self.modulestore.xblock_field_data_wrappers:
                    block._field_data = wrapper(block, block._field_data)  # pylint: disable=protected-access

                # decache any computed pending field settings
                block.save()
                return block
            except Exception:                   # pylint: disable=broad-except
                log.warning("Failed to load descriptor from %s", json_data, exc_info=True)
                return ErrorBlock.from_json(
                    json_data,
                    self,
                    location,
                    error_msg=exc_info_to_str(sys.exc_info())
                )

    def _convert_reference_to_key(self, ref_string):
        """
        Convert a single serialized UsageKey string in a ReferenceField into a UsageKey.
        """
        key = UsageKey.from_string(ref_string)
        return key.replace(run=self.modulestore.fill_in_run(key.course_key).run)

    def _convert_reference_fields_to_keys(self, class_, course_key, jsonfields):  # lint-amnesty, pylint: disable=unused-argument
        """
        Find all fields of type reference and convert the payload into UsageKeys
        :param class_: the XBlock class
        :param course_key: a CourseKey object for the given course
        :param jsonfields: a dict of the jsonified version of the fields
        """
        result = {}
        for field_name, value in jsonfields.items():
            field = class_.fields.get(field_name)
            if field is None:
                continue
            elif value is None:
                result[field_name] = value
            elif isinstance(field, Reference):
                result[field_name] = self._convert_reference_to_key(value)
            elif isinstance(field, ReferenceList):
                result[field_name] = [
                    self._convert_reference_to_key(ele) for ele in value
                ]
            elif isinstance(field, ReferenceValueDict):
                result[field_name] = {
                    key: self._convert_reference_to_key(subvalue) for key, subvalue in value.items()
                }
            else:
                result[field_name] = value
        return result

    def lookup_item(self, location):
        """
        Returns the JSON payload of the xblock at location.
        """

        try:
            json = self.module_data[location]
        except KeyError:
            json = self.modulestore._find_one(location)
            self.module_data[location] = json

        return json

    def get_edited_by(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edit_info.get('edited_by')

    def get_edited_on(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edit_info.get('edited_on')

    def get_subtree_edited_by(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edit_info.get('subtree_edited_by')

    def get_subtree_edited_on(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edit_info.get('subtree_edited_on')

    def get_published_by(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edit_info.get('published_by')

    def get_published_on(self, xblock):
        """
        See :class: cms.lib.xblock.runtime.EditInfoRuntimeMixin
        """
        return xblock._edit_info.get('published_date')

    def applicable_aside_types(self, block):
        # "old" mongo does support asides yet
        return []


# The only thing using this w/ wildcards is contentstore.mongo for asset retrieval
def location_to_query(location, wildcard=True, tag='i4x'):
    """
    Takes a Location and returns a SON object that will query for that location by subfields
    rather than subdoc.
    Fields in location that are None are ignored in the query.

    If `wildcard` is True, then a None in a location is treated as a wildcard
    query. Otherwise, it is searched for literally
    """
    query = location.to_deprecated_son(prefix='_id.', tag=tag)

    if wildcard:
        for key, value in query.items():
            # don't allow wildcards on revision, since public is set as None, so
            # its ambiguous between None as a real value versus None=wildcard
            if value is None and key != '_id.revision':
                del query[key]

    return query


def as_draft(location):
    """
    Returns the Location that is the draft for `location`
    If the location is in the DIRECT_ONLY_CATEGORIES, returns itself
    """
    if location.block_type in DIRECT_ONLY_CATEGORIES:
        return location
    return location.replace(revision=MongoRevisionKey.draft)


def as_published(location):
    """
    Returns the Location that is the published version for `location`
    """
    return location.replace(revision=MongoRevisionKey.published)


class MongoBulkOpsMixin(BulkOperationsMixin):
    """
    Mongo bulk operation support
    """

    def _end_outermost_bulk_operation(self, bulk_ops_record, structure_key):
        """
        The outermost nested bulk_operation call: do the actual end of the bulk operation.
        """
        return True

    def _is_in_bulk_operation(self, course_id, ignore_case=False):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Returns whether a bulk operation is in progress for the given course.
        """
        return super()._is_in_bulk_operation(
            course_id.for_branch(None), ignore_case
        )


class ParentLocationCache(dict):
    """
    Dict-based object augmented with a more cache-like interface, for internal use.
    """

    def has(self, key):
        return key in self

    def set(self, key, value):
        self[key] = value

    def delete_by_value(self, value):
        keys_to_delete = [k for k, v in self.items() if v == value]
        for key in keys_to_delete:
            del self[key]


class MongoModuleStore(ModuleStoreDraftAndPublished, ModuleStoreWriteBase, MongoBulkOpsMixin):
    """
    A Mongodb backed ModuleStore
    """

    # If no name is specified for the asset metadata collection, this name is used.
    DEFAULT_ASSET_COLLECTION_NAME = 'assetstore'

    # TODO (cpennington): Enable non-filesystem filestores
    # pylint: disable=invalid-name
    # pylint: disable=attribute-defined-outside-init
    def __init__(self, contentstore, doc_store_config, fs_root, render_template,
                 default_class=None,
                 error_tracker=null_error_tracker,
                 i18n_service=None,
                 fs_service=None,
                 user_service=None,
                 signal_handler=None,
                 retry_wait_time=0.1,
                 **kwargs):
        """
        :param doc_store_config: must have a host, db, and collection entries. Other common entries: port, tz_aware.
        """

        super().__init__(contentstore=contentstore, **kwargs)

        def do_connection(
            db, collection, host, port=27017, tz_aware=True, user=None, password=None, asset_collection=None, **kwargs
        ):
            """
            Create & open the connection, authenticate, and provide pointers to the collection
            """
            # Set a write concern of 1, which makes writes complete successfully to the primary
            # only before returning. Also makes pymongo report write errors.
            kwargs['w'] = 1

            self.database = connect_to_mongodb(
                db, host,
                port=port, tz_aware=tz_aware, user=user, password=password,
                retry_wait_time=retry_wait_time, **kwargs
            )

            self.collection = self.database[collection]

            # Collection which stores asset metadata.
            if asset_collection is None:
                asset_collection = self.DEFAULT_ASSET_COLLECTION_NAME
            self.asset_collection = self.database[asset_collection]

        do_connection(**doc_store_config)

        if default_class is not None:
            module_path, _, class_name = default_class.rpartition('.')
            try:
                class_ = getattr(import_module(module_path), class_name)
            except (ImportError, AttributeError):
                fallback_module_path = "xmodule.hidden_block"
                fallback_class_name = "HiddenBlock"
                log.exception(
                    "Failed to import the default store class. "
                    f"Falling back to {fallback_module_path}.{fallback_class_name}"
                )
                class_ = getattr(import_module(fallback_module_path), fallback_class_name)
            self.default_class = class_
        else:
            self.default_class = None
        self.fs_root = path(fs_root)
        self.error_tracker = error_tracker
        self.render_template = render_template
        self.i18n_service = i18n_service
        self.fs_service = fs_service
        self.user_service = user_service

        self._course_run_cache = {}
        self.signal_handler = signal_handler

    def close_connections(self):
        """
        Closes any open connections to the underlying database
        """
        self.collection.database.client.close()

    def _drop_database(self, database=True, collections=True, connections=True):
        """
        A destructive operation to drop the underlying database and close all connections.
        Intended to be used by test code for cleanup.

        If database is True, then this should drop the entire database.
        Otherwise, if collections is True, then this should drop all of the collections used
        by this modulestore.
        Otherwise, the modulestore should remove all data from the collections.

        If connections is True, then close the connection to the database as well.
        """
        # drop the assets
        super()._drop_database(database, collections, connections)

        connection = self.collection.database.client

        if database:
            connection.drop_database(self.collection.database.proxied_object)
        elif collections:
            self.collection.drop()
        else:
            self.collection.delete_many({})

        if connections:
            connection.close()

    @autoretry_read()
    def fill_in_run(self, course_key):
        """
        In mongo some course_keys are used without runs. This helper function returns
        a course_key with the run filled in, if the course does actually exist.
        """
        if course_key.run is not None:
            return course_key

        cache_key = (course_key.org, course_key.course)
        if cache_key not in self._course_run_cache:

            matching_courses = list(self.collection.find(SON([
                ('_id.tag', 'i4x'),
                ('_id.org', course_key.org),
                ('_id.course', course_key.course),
                ('_id.category', 'course'),
            ])).limit(1))

            if not matching_courses:
                return course_key

            self._course_run_cache[cache_key] = matching_courses[0]['_id']['name']

        return course_key.replace(run=self._course_run_cache[cache_key])

    def for_branch_setting(self, location):
        """
        Returns the Location that is for the current branch setting.
        """
        if location.block_type in DIRECT_ONLY_CATEGORIES:
            return location.replace(revision=MongoRevisionKey.published)
        if self.get_branch_setting() == ModuleStoreEnum.Branch.draft_preferred:
            return location.replace(revision=MongoRevisionKey.draft)
        return location.replace(revision=MongoRevisionKey.published)

    def _get_parent_cache(self, branch):
        """
        Provides a reference to one of the two branch-specific
        ParentLocationCaches associated with the current request (if any).
        """
        if self.request_cache is not None:
            return self.request_cache.data.setdefault(f'parent-location-{branch}', ParentLocationCache())
        else:
            return ParentLocationCache()

    def _compute_metadata_inheritance_tree(self, course_id):
        '''
        Find all inheritable fields from all xblocks in the course which may define inheritable data
        '''
        # get all collections in the course, this query should not return any leaf nodes
        course_id = self.fill_in_run(course_id)
        query = SON([
            ('_id.tag', 'i4x'),
            ('_id.org', course_id.org),
            ('_id.course', course_id.course),
            ('_id.category', {'$in': BLOCK_TYPES_WITH_CHILDREN})
        ])
        # if we're only dealing in the published branch, then only get published containers
        if self.get_branch_setting() == ModuleStoreEnum.Branch.published_only:
            query['_id.revision'] = None
        # we just want the Location, children, and inheritable metadata
        record_filter = {'_id': 1, 'definition.children': 1}

        # just get the inheritable metadata since that is all we need for the computation
        # this minimizes both data pushed over the wire
        for field_name in InheritanceMixin.fields:
            record_filter[f'metadata.{field_name}'] = 1

        # call out to the DB
        resultset = self.collection.find(query, record_filter)

        # it's ok to keep these as deprecated strings b/c the overall cache is indexed by course_key and this
        # is a dictionary relative to that course
        results_by_url = {}
        root = None

        # now go through the results and order them by the location url
        for result in resultset:
            # manually pick it apart b/c the db has tag and we want as_published revision regardless
            location = as_published(BlockUsageLocator._from_deprecated_son(result['_id'], course_id.run))

            location_url = str(location)
            if location_url in results_by_url:
                # found either draft or live to complement the other revision
                # FIXME this is wrong. If the child was moved in draft from one parent to the other, it will
                # show up under both in this logic: https://openedx.atlassian.net/browse/TNL-1075
                existing_children = results_by_url[location_url].get('definition', {}).get('children', [])
                additional_children = result.get('definition', {}).get('children', [])
                total_children = existing_children + additional_children
                # use set to get rid of duplicates. We don't care about order; so, it shouldn't matter.
                results_by_url[location_url].setdefault('definition', {})['children'] = set(total_children)
            else:
                results_by_url[location_url] = result
            if location.block_type == 'course':  # pylint: disable=no-member
                root = location_url

        # now traverse the tree and compute down the inherited metadata
        metadata_to_inherit = {}

        def _compute_inherited_metadata(url):
            """
            Helper method for computing inherited metadata for a specific location url
            """
            my_metadata = results_by_url[url].get('metadata', {})

            # go through all the children and recurse, but only if we have
            # in the result set. Remember results will not contain leaf nodes
            for child in results_by_url[url].get('definition', {}).get('children', []):
                if child in results_by_url:
                    new_child_metadata = copy.deepcopy(my_metadata)
                    new_child_metadata.update(results_by_url[child].get('metadata', {}))
                    results_by_url[child]['metadata'] = new_child_metadata
                    metadata_to_inherit[child] = new_child_metadata
                    _compute_inherited_metadata(child)
                else:
                    # this is likely a leaf node, so let's record what metadata we need to inherit
                    metadata_to_inherit[child] = my_metadata.copy()
                # WARNING: 'parent' is not part of inherited metadata, but
                # we're piggybacking on this recursive traversal to grab
                # and cache the child's parent, as a performance optimization.
                # The 'parent' key will be popped out of the dictionary during
                # CachingDescriptorSystem.load_item
                metadata_to_inherit[child].setdefault('parent', {})[self.get_branch_setting()] = url

        if root is not None:
            _compute_inherited_metadata(root)

        return metadata_to_inherit

    def _clean_item_data(self, item):
        """
        Renames the '_id' field in item to 'location'
        """
        item['location'] = item['_id']
        del item['_id']

    @autoretry_read()
    def _query_children_for_cache_children(self, course_key, items):
        """
        Generate a pymongo in query for finding the items and return the payloads
        """
        # first get non-draft in a round-trip
        query = {
            '_id': {'$in': [
                UsageKey.from_string(item).map_into_course(course_key).to_deprecated_son() for item in items
            ]}
        }
        return list(self.collection.find(query))

    def _cache_children(self, course_key, items, depth=0):
        """
        Returns a dictionary mapping Location -> item data, populated with json data
        for all descendents of items up to the specified depth.
        (0 = no descendents, 1 = children, 2 = grandchildren, etc)
        If depth is None, will load all the children.
        This will make a number of queries that is linear in the depth.
        """

        data = {}
        to_process = list(items)
        course_key = self.fill_in_run(course_key)
        parent_cache = self._get_parent_cache(self.get_branch_setting())

        while to_process and (depth is None or depth >= 0):
            children = []
            for item in to_process:
                self._clean_item_data(item)
                item_location = BlockUsageLocator._from_deprecated_son(item['location'], course_key.run)
                item_children = item.get('definition', {}).get('children', [])
                children.extend(item_children)
                for item_child in item_children:
                    parent_cache.set(item_child, item_location)
                data[item_location] = item

            if depth == 0:
                break

            # Load all children by id. See
            # http://www.mongodb.org/display/DOCS/Advanced+Queries#AdvancedQueries-%24or
            # for or-query syntax
            to_process = []
            if children:
                to_process = self._query_children_for_cache_children(course_key, children)

            # If depth is None, then we just recurse until we hit all the descendents
            if depth is not None:
                depth -= 1

        return data

    def _load_item(self, course_key, item, data_cache,
                   using_descriptor_system=None, for_parent=None):
        """
        Load an XModuleDescriptor from item, using the children stored in data_cache

        Arguments:
            course_key (CourseKey): which course to load from
            item (dict): A dictionary with the following keys:
                location: The serialized UsageKey for the item to load
                data_dir (optional): The directory name to use as the root data directory for this XModule
            data_cache (dict): A dictionary mapping from UsageKeys to xblock field data
                (this is the xblock data loaded from the database)
            using_descriptor_system (CachingDescriptorSystem): The existing CachingDescriptorSystem
                to add data to, and to load the XBlocks from.
            for_parent (:class:`XBlock`): The parent of the XBlock being loaded.
        """
        course_key = self.fill_in_run(course_key)
        location = BlockUsageLocator._from_deprecated_son(item['location'], course_key.run)
        data_dir = getattr(item, 'data_dir', location.course)
        root = self.fs_root / data_dir
        resource_fs = _OSFS_INSTANCE.setdefault(root, OSFS(root, create=True))

        if using_descriptor_system is None:
            services = {}
            if self.i18n_service:
                services["i18n"] = self.i18n_service

            if self.fs_service:
                services["fs"] = self.fs_service

            if self.user_service:
                services["user"] = self.user_service
            services["settings"] = SettingsService()

            if self.request_cache:
                services["request_cache"] = self.request_cache

            services["partitions"] = PartitionService(course_key)

            system = CachingDescriptorSystem(
                modulestore=self,
                course_key=course_key,
                module_data=data_cache,
                default_class=self.default_class,
                resources_fs=resource_fs,
                error_tracker=self.error_tracker,
                render_template=self.render_template,
                mixins=self.xblock_mixins,
                select=self.xblock_select,
                disabled_xblock_types=self.disabled_xblock_types,
                services=services,
            )
        else:
            system = using_descriptor_system
            system.module_data.update(data_cache)

        item = system.get_block(location, for_parent=for_parent)

        # TODO Once TNL-5092 is implemented, we can remove the following line
        # of code. Until then, set the course_version field on the block to be
        # consistent with the Split modulestore. Since Mongo modulestore doesn't
        # maintain course versions set it to None.
        item.course_version = None
        return item

    def _load_items(self, course_key, items, depth=0, using_descriptor_system=None, for_parent=None):
        """
        Load a list of xblocks from the data in items, with children cached up
        to specified depth
        """
        course_key = self.fill_in_run(course_key)
        data_cache = self._cache_children(course_key, items, depth)

        # if we are loading a course object, if we're not prefetching children (depth != 0) then don't
        # bother with the metadata inheritance
        return [
            self._load_item(
                course_key,
                item,
                data_cache,
                using_descriptor_system=using_descriptor_system,
                for_parent=for_parent,
            )
            for item in items
        ]

    @autoretry_read()
    def get_course_summaries(self, **kwargs):
        """
        Returns a list of `CourseSummary`. This accepts an optional parameter of 'org' which
        will apply an efficient filter to only get courses with the specified ORG
        """
        def extract_course_summary(course):
            """
            Extract course information from the course block for mongo.
            """
            return {
                field: course['metadata'][field]
                for field in CourseSummary.course_info_fields
                if field in course['metadata']
            }

        course_records = []
        query = {'_id.category': 'course'}
        course_org_filter = kwargs.get('org')
        course_keys = kwargs.get('course_keys')

        if course_keys:
            course_queries = []
            for course_key in course_keys:
                course_query = {
                    f'_id.{value_attr}': getattr(course_key, key_attr)
                    for key_attr, value_attr in {'org': 'org', 'course': 'course', 'run': 'name'}.items()
                }
                course_query.update(query)
                course_queries.append(course_query)
            query = {'$or': course_queries}
        elif course_org_filter:
            query['_id.org'] = course_org_filter

        course_records = self.collection.find(query, {'metadata': True})

        courses_summaries = []
        for course in course_records:
            if not (course['_id']['org'] == 'edx' and course['_id']['course'] == 'templates'):
                locator = CourseKey.from_string('/'.join(
                    [course['_id']['org'], course['_id']['course'], course['_id']['name']]
                ))
                course_summary = extract_course_summary(course)
                courses_summaries.append(
                    CourseSummary(locator, **course_summary)
                )

        return courses_summaries

    @autoretry_read()
    def get_courses(self, **kwargs):
        '''
        Returns a list of course descriptors. This accepts an optional parameter of 'org' which
        will apply an efficient filter to only get courses with the specified ORG
        '''

        course_org_filter = kwargs.get('org')

        if course_org_filter:
            course_records = self.collection.find({'_id.category': 'course', '_id.org': course_org_filter})
        else:
            course_records = self.collection.find({'_id.category': 'course'})

        base_list = sum(
            [
                self._load_items(
                    CourseKey.from_string('/'.join(
                        [course['_id']['org'], course['_id']['course'], course['_id']['name']]
                    )),
                    [course]
                )
                for course
                # I tried to add '$and': [{'_id.org': {'$ne': 'edx'}}, {'_id.course': {'$ne': 'templates'}}]
                # but it didn't do the right thing (it filtered all edx and all templates out)
                in course_records
                if not (  # TODO kill this
                    course['_id']['org'] == 'edx' and
                    course['_id']['course'] == 'templates'
                )
            ],
            []
        )
        return [course for course in base_list if not isinstance(course, ErrorBlock)]

    @autoretry_read()
    def _find_one(self, location):
        '''Look for a given location in the collection. If the item is not present, raise
        ItemNotFoundError.
        '''
        assert isinstance(location, UsageKey)
        item = self.collection.find_one(
            {'_id': location.to_deprecated_son()}
        )
        if item is None:
            raise ItemNotFoundError(location)
        return item

    def make_course_key(self, org, course, run):
        """
        Return a valid :class:`~opaque_keys.edx.keys.CourseKey` for this modulestore
        that matches the supplied `org`, `course`, and `run`.

        This key may represent a course that doesn't exist in this modulestore.
        """
        return CourseLocator(org, course, run, deprecated=True)

    def make_course_usage_key(self, course_key):
        """
        Return a valid :class:`~opaque_keys.edx.keys.UsageKey` for this modulestore
        that matches the supplied course_key.
        """
        return BlockUsageLocator(course_key, 'course', course_key.run)

    def get_course(self, course_key, depth=0, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Get the course with the given courseid (org/course/run)
        """
        assert isinstance(course_key, CourseKey)

        if not course_key.deprecated:  # split course_key
            # The supplied CourseKey is of the wrong type, so it can't possibly be stored in this modulestore.
            raise ItemNotFoundError(course_key)

        course_key = self.fill_in_run(course_key)
        location = course_key.make_usage_key('course', course_key.run)
        try:
            return self.get_item(location, depth=depth)
        except ItemNotFoundError:
            return None

    @autoretry_read()
    def has_course(self, course_key, ignore_case=False, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Returns the course_id of the course if it was found, else None
        Note: we return the course_id instead of a boolean here since the found course may have
           a different id than the given course_id when ignore_case is True.

        If ignore_case is True, do a case insensitive search,
        otherwise, do a case sensitive search
        """
        assert isinstance(course_key, CourseKey)

        if not course_key.deprecated:  # split course_key
            # The supplied CourseKey is of the wrong type, so it can't possibly be stored in this modulestore.
            return False

        if isinstance(course_key, LibraryLocator):
            return None  # Libraries require split mongo
        course_key = self.fill_in_run(course_key)
        location = course_key.make_usage_key('course', course_key.run)
        if ignore_case:
            course_query = location.to_deprecated_son('_id.')
            for key in course_query.keys():
                if isinstance(course_query[key], str):
                    course_query[key] = re.compile(r"(?i)^{}$".format(course_query[key]))
        else:
            course_query = {'_id': location.to_deprecated_son()}
        course = self.collection.find_one(course_query, projection={'_id': True})
        if course:
            return CourseKey.from_string('/'.join([
                course['_id']['org'], course['_id']['course'], course['_id']['name']]
            ))
        else:
            return None

    def has_item(self, usage_key):
        """
        Returns True if location exists in this ModuleStore.
        """
        try:
            self._find_one(usage_key)
            return True
        except ItemNotFoundError:
            return False

    def get_item(self, usage_key, depth=0, using_descriptor_system=None, for_parent=None, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Returns an XModuleDescriptor instance for the item at location.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        Arguments:
            usage_key: a :class:`.UsageKey` instance
            depth (int): An argument that some module stores may use to prefetch
                descendents of the queried blocks for more efficient results later
                in the request. The depth is counted in the number of
                calls to get_children() to cache. None indicates to cache all descendents.
            using_descriptor_system (CachingDescriptorSystem): The existing CachingDescriptorSystem
                to add data to, and to load the XBlocks from.
        """
        item = self._find_one(usage_key)
        block = self._load_items(
            usage_key.course_key,
            [item],
            depth,
            using_descriptor_system=using_descriptor_system,
            for_parent=for_parent,
        )[0]
        return block

    @staticmethod
    def _course_key_to_son(course_id, tag='i4x'):
        """
        Generate the partial key to look up items relative to a given course
        """
        return SON([
            ('_id.tag', tag),
            ('_id.org', course_id.org),
            ('_id.course', course_id.course),
        ])

    @staticmethod
    def _id_dict_to_son(id_dict):
        """
        Generate the partial key to look up items relative to a given course
        """
        return SON([
            (key, id_dict[key])
            for key in ('tag', 'org', 'course', 'category', 'name', 'revision')
        ])

    @autoretry_read()
    def get_items(  # lint-amnesty, pylint: disable=arguments-differ
            self,
            course_id,
            settings=None,
            content=None,
            key_revision=MongoRevisionKey.published,
            qualifiers=None,
            using_descriptor_system=None,
            **kwargs
    ):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_id

        NOTE: don't use this to look for courses
        as the course_id is required. Use get_courses which is a lot faster anyway.

        If you don't provide a value for revision, this limits the result to only ones in the
        published course. Call this method on draft mongo store if you want to include drafts.

        Args:
            course_id (CourseKey): the course identifier
            settings (dict): fields to look for which have settings scope. Follows same syntax
                and rules as qualifiers below
            content (dict): fields to look for which have content scope. Follows same syntax and
                rules as qualifiers below.
            key_revision (str): the revision of the items you're looking for.
                MongoRevisionKey.draft - only returns drafts
                MongoRevisionKey.published (equates to None) - only returns published
                If you want one of each matching xblock but preferring draft to published, call this same method
                on the draft modulestore with ModuleStoreEnum.RevisionOption.draft_preferred.
            qualifiers (dict): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                Substring matching pass a regex object.
                For this modulestore, ``name`` is a commonly provided key (Location based stores)
                This modulestore does not allow searching dates by comparison or edited_by, previous_version,
                update_version info.
            using_descriptor_system (CachingDescriptorSystem): The existing CachingDescriptorSystem
                to add data to, and to load the XBlocks from.
        """
        qualifiers = qualifiers.copy() if qualifiers else {}  # copy the qualifiers (destructively manipulated here)
        query = self._course_key_to_son(course_id)
        query['_id.revision'] = key_revision
        for field in ['category', 'name']:
            if field in qualifiers:
                qualifier_value = qualifiers.pop(field)
                if isinstance(qualifier_value, list):
                    qualifier_value = {'$in': qualifier_value}
                query['_id.' + field] = qualifier_value

        for key, value in (settings or {}).items():
            query['metadata.' + key] = value
        for key, value in (content or {}).items():
            query['definition.data.' + key] = value
        if 'children' in qualifiers:
            query['definition.children'] = qualifiers.pop('children')

        query.update(qualifiers)
        items = self.collection.find(
            query,
            sort=[SORT_REVISION_FAVOR_DRAFT],
        )

        blocks = self._load_items(
            course_id,
            list(items),
            using_descriptor_system=using_descriptor_system
        )
        return blocks

    def create_course(self, org, course, run, user_id, fields=None, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Creates and returns the course.

        Args:
            org (str): the organization that owns the course
            course (str): the name of the course
            run (str): the name of the run
            user_id: id of the user creating the course
            fields (dict): Fields to set on the course at initialization
            kwargs: Any optional arguments understood by a subset of modulestores to customize instantiation

        Returns: a CourseBlock

        Raises:
            InvalidLocationError: If a course with the same org, course, and run already exists
        """
        course_id = CourseKey.from_string('/'.join([org, course, run]))

        # Check if a course with this org/course has been defined before (case-insensitive)
        course_search_location = SON([
            ('_id.tag', 'i4x'),
            ('_id.org', re.compile(f'^{course_id.org}$', re.IGNORECASE)),
            ('_id.course', re.compile(f'^{course_id.course}$', re.IGNORECASE)),
            ('_id.category', 'course'),
        ])
        courses = self.collection.find(course_search_location, projection={'_id': True})
        try:
            course = courses.next()
            raise DuplicateCourseError(course_id, course['_id'])
        except StopIteration:
            pass

        with self.bulk_operations(course_id):
            xblock = self.create_item(user_id, course_id, 'course', course_id.run, fields=fields, **kwargs)

            # create any other necessary things as a side effect
            super().create_course(
                org, course, run, user_id, runtime=xblock.runtime, **kwargs
            )

            return xblock

    def create_xblock(
        self, runtime, course_key, block_type, block_id=None, fields=None,
        metadata=None, definition_data=None, **kwargs
    ):
        """
        Create the new xblock but don't save it. Returns the new block.

        :param runtime: if you already have an xblock from the course, the xblock.runtime value
        :param fields: a dictionary of field names and values for the new xblock
        """
        if metadata is None:
            metadata = {}

        if definition_data is None:
            definition_data = {}

        # @Cale, should this use LocalId like we do in split?
        if block_id is None:
            if block_type == 'course':
                block_id = course_key.run
            else:
                block_id = '{}_{}'.format(block_type, uuid4().hex[:5])

        if runtime is None:
            services = {}
            if self.i18n_service:
                services["i18n"] = self.i18n_service

            if self.fs_service:
                services["fs"] = self.fs_service

            if self.user_service:
                services["user"] = self.user_service

            services["partitions"] = PartitionService(course_key)

            runtime = CachingDescriptorSystem(
                modulestore=self,
                module_data={},
                course_key=course_key,
                default_class=self.default_class,
                resources_fs=None,
                error_tracker=self.error_tracker,
                render_template=self.render_template,
                mixins=self.xblock_mixins,
                select=self.xblock_select,
                services=services,
            )
        xblock_class = runtime.load_block_type(block_type)
        location = course_key.make_usage_key(block_type, block_id)
        dbmodel = self._create_new_field_data(block_type, location, definition_data, metadata)
        xblock = runtime.construct_xblock_from_class(
            xblock_class,
            # We're loading a descriptor, so student_id is meaningless
            # We also don't have separate notions of definition and usage ids yet,
            # so we use the location for both.
            ScopeIds(None, block_type, location, location),
            dbmodel,
            for_parent=kwargs.get('for_parent'),
        )
        if fields is not None:
            for key, value in fields.items():
                setattr(xblock, key, value)
        # decache any pending field settings from init
        xblock.save()
        return xblock

    def create_item(self, user_id, course_key, block_type, block_id=None, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Creates and saves a new item in a course.

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xblock
            course_key: A :class:`~opaque_keys.edx.CourseKey` identifying which course to create
                this item in
            block_type: The typo of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
        """
        if block_id is None:
            if block_type == 'course':
                block_id = course_key.run
            else:
                block_id = '{}_{}'.format(block_type, uuid4().hex[:5])

        runtime = kwargs.pop('runtime', None)
        xblock = self.create_xblock(runtime, course_key, block_type, block_id, **kwargs)
        xblock = self.update_item(xblock, user_id, allow_not_found=True)

        return xblock

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Creates and saves a new xblock that as a child of the specified block

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xblock
            parent_usage_key: a :class:`~opaque_key.edx.UsageKey` identifing the
                block that this item should be parented under
            block_type: The typo of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
        """
        # attach to parent if given
        parent = None

        if parent_usage_key is not None:
            parent = self.get_item(parent_usage_key)
            kwargs.setdefault('for_parent', parent)

        xblock = self.create_item(user_id, parent_usage_key.course_key, block_type, block_id=block_id, **kwargs)

        if parent is not None and 'detached' not in xblock._class_tags:
            # Originally added to support entrance exams (settings.FEATURES.get('ENTRANCE_EXAMS'))
            if kwargs.get('position') is None:
                parent.children.append(xblock.location)
            else:
                parent.children.insert(kwargs.get('position'), xblock.location)

            self.update_item(parent, user_id, child_update=True)  # lint-amnesty, pylint: disable=unexpected-keyword-arg

        return xblock

    def import_xblock(self, user_id, course_key, block_type, block_id, fields=None, runtime=None, **kwargs):
        """
        Simple implementation of overwriting any existing xblock
        """
        if block_type == 'course':
            block_id = course_key.run
        xblock = self.create_xblock(runtime, course_key, block_type, block_id, fields)
        return self.update_item(xblock, user_id, allow_not_found=True)

    def _get_course_for_item(self, location, depth=0):
        '''
        for a given XBlock, return the course that it belongs to
        Also we have to assert that this block maps to only one course item - it'll throw an
        assert if not
        '''
        return self.get_course(location.course_key, depth)

    def _update_single_item(self, location, update, allow_not_found=False):
        """
        Set update on the specified item, and raises ItemNotFoundError
        if the location doesn't exist
        """
        bulk_record = self._get_bulk_ops_record(location.course_key)
        bulk_record.dirty = True
        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        result = self.collection.update_one(
            {'_id': location.to_deprecated_son()},
            {'$set': update},
            upsert=allow_not_found,
        )
        if result.matched_count == 0 and result.upserted_id is None:
            raise ItemNotFoundError(location)

    def _update_ancestors(self, location, update):
        """
        Recursively applies update to all the ancestors of location
        """
        parent = self._get_raw_parent_location(as_published(location), ModuleStoreEnum.RevisionOption.draft_preferred)
        if parent:
            self._update_single_item(parent, update)
            self._update_ancestors(parent, update)

    def update_item(self, xblock, user_id, allow_not_found=False, force=False, isPublish=False,  # lint-amnesty, pylint: disable=arguments-differ
                    is_publish_root=True):
        """
        Update the persisted version of xblock to reflect its current values.

        xblock: which xblock to persist
        user_id: who made the change (ignored for now by this modulestore)
        allow_not_found: whether to create a new object if one didn't already exist or give an error
        force: force is meaningless for this modulestore
        isPublish: an internal parameter that indicates whether this update is due to a Publish operation, and
          thus whether the item's published information should be updated.
        is_publish_root: when publishing, this indicates whether xblock is the root of the publish and should
          therefore propagate subtree edit info up the tree
        """
        course_key = xblock.location.course_key

        try:
            definition_data = self._serialize_scope(xblock, Scope.content)
            now = datetime.now(UTC)
            payload = {
                'definition.data': definition_data,
                'metadata': self._serialize_scope(xblock, Scope.settings),
                'edit_info': {
                    'edited_on': now,
                    'edited_by': user_id,
                    'subtree_edited_on': now,
                    'subtree_edited_by': user_id,
                }
            }

            if isPublish:
                payload['edit_info']['published_date'] = now
                payload['edit_info']['published_by'] = user_id
            elif 'published_date' in getattr(xblock, '_edit_info', {}):
                payload['edit_info']['published_date'] = xblock._edit_info['published_date']
                payload['edit_info']['published_by'] = xblock._edit_info['published_by']

            if xblock.has_children:
                children = self._serialize_scope(xblock, Scope.children)
                payload.update({'definition.children': children['children']})

                # Remove all old pointers to me, then add my current children back
                parent_cache = self._get_parent_cache(self.get_branch_setting())
                parent_cache.delete_by_value(xblock.location)
                for child in xblock.children:
                    parent_cache.set(str(child), xblock.location)

            self._update_single_item(xblock.scope_ids.usage_id, payload, allow_not_found=allow_not_found)

            # update subtree edited info for ancestors
            # don't update the subtree info for descendants of the publish root for efficiency
            if not isPublish or (isPublish and is_publish_root):
                ancestor_payload = {
                    'edit_info.subtree_edited_on': now,
                    'edit_info.subtree_edited_by': user_id
                }
                self._update_ancestors(xblock.scope_ids.usage_id, ancestor_payload)

            # update the edit info of the instantiated xblock
            xblock._edit_info = payload['edit_info']
            # fire signal that we've written to DB
        except ItemNotFoundError:
            if not allow_not_found:  # lint-amnesty, pylint: disable=no-else-raise
                raise
            elif not self.has_course(course_key):
                raise ItemNotFoundError(course_key)  # lint-amnesty, pylint: disable=raise-missing-from

        return xblock

    def _serialize_scope(self, xblock, scope):
        """
        Find all fields of type reference and convert the payload from UsageKeys to deprecated strings
        :param xblock: the XBlock class
        :param jsonfields: a dict of the jsonified version of the fields
        """
        jsonfields = {}
        for field_name, field in xblock.fields.items():
            if field.scope == scope and field.is_set_on(xblock):
                if field.scope == Scope.parent:
                    continue
                elif isinstance(field, Reference):
                    jsonfields[field_name] = str(field.read_from(xblock))
                elif isinstance(field, ReferenceList):
                    jsonfields[field_name] = [
                        str(ele) for ele in field.read_from(xblock)
                    ]
                elif isinstance(field, ReferenceValueDict):
                    jsonfields[field_name] = {
                        key: str(subvalue) for key, subvalue in field.read_from(xblock).items()
                    }
                else:
                    jsonfields[field_name] = field.read_json(xblock)
        return jsonfields

    def _get_non_orphan_parents(self, location, parents, revision):
        """
        Extract non orphan parents by traversing the list of possible parents and remove current location
        from orphan parents to avoid parents calculation overhead next time.
        """
        non_orphan_parents = []
        # get bulk_record once rather than for each iteration
        bulk_record = self._get_bulk_ops_record(location.course_key)

        for parent in parents:
            parent_loc = BlockUsageLocator._from_deprecated_son(parent['_id'], location.course_key.run)

            # travel up the tree for orphan validation
            ancestor_loc = parent_loc
            while ancestor_loc is not None:
                current_loc = ancestor_loc
                ancestor_loc = self._get_raw_parent_location(as_published(current_loc), revision)
                if ancestor_loc is None:
                    bulk_record.dirty = True
                    # The parent is an orphan, so remove all the children including
                    # the location whose parent we are looking for from orphan parent
                    self.collection.update_one(
                        {'_id': parent_loc.to_deprecated_son()},
                        {'$set': {'definition.children': []}},
                        upsert=True,
                    )
                elif ancestor_loc.block_type == 'course':
                    # once we reach the top location of the tree and if the location is not an orphan then the
                    # parent is not an orphan either
                    non_orphan_parents.append(parent_loc)
                    break

        return non_orphan_parents

    def _get_raw_parent_location(self, location, revision=ModuleStoreEnum.RevisionOption.published_only):
        '''
        Helper for get_parent_location that finds the location that is the parent of this location in this course,
        but does NOT return a version agnostic location.
        '''
        assert location.branch is None
        assert revision == ModuleStoreEnum.RevisionOption.published_only \
            or revision == ModuleStoreEnum.RevisionOption.draft_preferred  # lint-amnesty, pylint: disable=consider-using-in

        parent_cache = self._get_parent_cache(self.get_branch_setting())
        if parent_cache.has(str(location)):
            return parent_cache.get(str(location))

        # create a query with tag, org, course, and the children field set to the given location
        query = self._course_key_to_son(location.course_key)
        query['definition.children'] = str(location)

        # if only looking for the PUBLISHED parent, set the revision in the query to None
        if revision == ModuleStoreEnum.RevisionOption.published_only:
            query['_id.revision'] = MongoRevisionKey.published

        def cache_and_return(parent_loc):
            parent_cache.set(str(location), parent_loc)
            return parent_loc

        # query the collection, sorting by DRAFT first
        parents = list(
            self.collection.find(query, {'_id': True}, sort=[SORT_REVISION_FAVOR_DRAFT])
        )
        if len(parents) == 0:
            # no parents were found
            return cache_and_return(None)

        if revision == ModuleStoreEnum.RevisionOption.published_only:
            if len(parents) > 1:
                non_orphan_parents = self._get_non_orphan_parents(location, parents, revision)
                if len(non_orphan_parents) == 0:
                    # no actual parent found
                    return cache_and_return(None)

                if len(non_orphan_parents) > 1:  # lint-amnesty, pylint: disable=no-else-raise
                    # should never have multiple PUBLISHED parents
                    raise ReferentialIntegrityError(
                        "{} parents claim {}".format(len(parents), location)
                    )
                else:
                    return cache_and_return(non_orphan_parents[0].replace(run=location.course_key.run))
            else:
                # return the single PUBLISHED parent
                return cache_and_return(BlockUsageLocator._from_deprecated_son(parents[0]['_id'],
                                                                               location.course_key.run))
        else:
            # there could be 2 different parents if
            #   (1) the draft item was moved or
            #   (2) the parent itself has 2 versions: DRAFT and PUBLISHED
            #  if there are multiple parents with version PUBLISHED then choose from non-orphan parents
            all_parents = []
            published_parents = 0
            for parent in parents:
                if parent['_id']['revision'] is None:
                    published_parents += 1
                all_parents.append(parent)

            # since we sorted by SORT_REVISION_FAVOR_DRAFT, the 0'th parent is the one we want
            if published_parents > 1:
                non_orphan_parents = self._get_non_orphan_parents(location, all_parents, revision)
                return cache_and_return(non_orphan_parents[0].replace(run=location.course_key.run))

            found_id = all_parents[0]['_id']
            # don't disclose revision outside modulestore
            return cache_and_return(BlockUsageLocator._from_deprecated_son(found_id, location.course_key.run))

    def get_parent_location(self, location, revision=ModuleStoreEnum.RevisionOption.published_only, **kwargs):
        '''
        Find the location that is the parent of this location in this course.

        Returns: version agnostic location (revision always None) as per the rest of mongo.

        Args:
            revision:
                ModuleStoreEnum.RevisionOption.published_only
                    - return only the PUBLISHED parent if it exists, else returns None
                ModuleStoreEnum.RevisionOption.draft_preferred
                    - return either the DRAFT or PUBLISHED parent,
                        preferring DRAFT, if parent(s) exists,
                        else returns None
        '''
        parent = self._get_raw_parent_location(location, revision)
        if parent:
            return parent
        return None

    def get_modulestore_type(self, course_key=None):  # lint-amnesty, pylint: disable=arguments-differ, unused-argument
        """
        Returns an enumeration-like type reflecting the type of this modulestore per ModuleStoreEnum.Type
        Args:
            course_key: just for signature compatibility
        """
        return ModuleStoreEnum.Type.mongo

    def get_orphans(self, course_key, **kwargs):
        """
        Return an array of all of the locations for orphans in the course.
        """
        course_key = self.fill_in_run(course_key)
        detached_categories = [name for name, __ in XBlock.load_tagged_classes("detached")]
        query = self._course_key_to_son(course_key)
        query['_id.category'] = {'$nin': detached_categories}
        all_items = self.collection.find(query)
        all_reachable = set()
        item_locs = set()
        for item in all_items:
            if item['_id']['category'] != 'course':
                # It would be nice to change this method to return UsageKeys instead of the deprecated string.
                item_locs.add(
                    str(as_published(BlockUsageLocator._from_deprecated_son(item['_id'], course_key.run)))
                )
            all_reachable = all_reachable.union(item.get('definition', {}).get('children', []))
        item_locs -= all_reachable
        return [UsageKey.from_string(item_loc).map_into_course(course_key) for item_loc in item_locs]

    def get_courses_for_wiki(self, wiki_slug, **kwargs):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course keys
        """
        courses = self.collection.find(
            {'_id.category': 'course', 'definition.data.wiki_slug': wiki_slug},
            {'_id': True}
        )
        # the course's run == its name. It's the only xblock for which that's necessarily true.
        return [
            BlockUsageLocator._from_deprecated_son(course['_id'], course['_id']['name']).course_key
            for course in courses
        ]

    def _create_new_field_data(self, _category, _location, definition_data, metadata):
        """
        To instantiate a new xblock which will be saved later, set up the dbModel and kvs
        """
        kvs = MongoKeyValueStore(
            definition_data,
            None,
            [],
            metadata,
        )

        field_data = KvsFieldData(kvs)
        return field_data

    def _find_course_assets(self, course_key):
        """
        Internal; finds (or creates) course asset info about all assets for a particular course

        Arguments:
            course_key (CourseKey): course identifier

        Returns:
            CourseAssetsFromStorage object, wrapping the relevant Mongo doc. If asset metadata
            exists, other keys will be the other asset types with values as lists of asset metadata.
        """
        # Using the course_key, find or insert the course asset metadata document.
        # A single document exists per course to store the course asset metadata.
        course_key = self.fill_in_run(course_key)
        if course_key.run is None:
            log.warning('No run found for combo org "{}" course "{}" on asset request.'.format(
                course_key.org, course_key.course
            ))
            course_assets = None
        else:
            # Complete course key, so query for asset metadata.
            course_assets = self.asset_collection.find_one(
                {'course_id': str(course_key)},
            )

        doc_id = None if course_assets is None else course_assets['_id']
        if course_assets is None:
            # Check to see if the course is created in the course collection.
            if self.get_course(course_key) is None:  # lint-amnesty, pylint: disable=no-else-raise
                raise ItemNotFoundError(course_key)
            else:
                # Course exists, so create matching assets document.
                course_assets = {'course_id': str(course_key), 'assets': {}}
                doc_id = self.asset_collection.insert_one(course_assets).inserted_id
        elif isinstance(course_assets['assets'], list):
            # This record is in the old course assets format.
            # Ensure that no data exists before updating the format.
            assert len(course_assets['assets']) == 0
            # Update the format to a dict.
            self.asset_collection.update_one(
                {'_id': doc_id},
                {'$set': {'assets': {}}}
            )

        # Pass back wrapped 'assets' dict with the '_id' key added to it for document update purposes.
        return CourseAssetsFromStorage(course_key, doc_id, course_assets['assets'])

    def _make_mongo_asset_key(self, asset_type):
        """
        Given a asset type, form a key needed to update the proper embedded field in the Mongo doc.
        """
        return f'assets.{asset_type}'

    def _save_asset_metadata_list(self, asset_metadata_list, user_id, import_only):
        """
        Internal; saves the info for a particular course's asset.

        Arguments:
            asset_metadata_list (list(AssetMetadata)): list of data about several course assets
            user_id (int|long): user ID saving the asset metadata
            import_only (bool): True if edited_on/by data should remain unchanged.
        """
        course_key = asset_metadata_list[0].asset_id.course_key
        course_assets = self._find_course_assets(course_key)
        assets_by_type = self._save_assets_by_type(course_key, asset_metadata_list, course_assets, user_id, import_only)

        # Build an update set with potentially multiple embedded fields.
        updates_by_type = {}
        for asset_type, assets in assets_by_type.items():
            updates_by_type[self._make_mongo_asset_key(asset_type)] = list(assets)

        # Update the document.
        self.asset_collection.update_one(
            {'_id': course_assets.doc_id},
            {'$set': updates_by_type}
        )
        return True

    def save_asset_metadata(self, asset_metadata, user_id, import_only=False):
        """
        Saves the info for a particular course's asset.

        Arguments:
            asset_metadata (AssetMetadata): data about the course asset data
            user_id (int|long): user ID saving the asset metadata
            import_only (bool): True if importing without editing, False if editing

        Returns:
            True if info save was successful, else False
        """
        return self._save_asset_metadata_list([asset_metadata, ], user_id, import_only)

    def save_asset_metadata_list(self, asset_metadata_list, user_id, import_only=False):
        """
        Saves the asset metadata for each asset in a list of asset metadata.
        Optimizes the saving of many assets.

        Args:
            asset_metadata (AssetMetadata): data about the course asset data
            user_id (int|long): user ID saving the asset metadata
            import_only (bool): True if importing without editing, False if editing

        Returns:
            True if info save was successful, else False
        """
        return self._save_asset_metadata_list(asset_metadata_list, user_id, import_only)

    def copy_all_asset_metadata(self, source_course_key, dest_course_key, user_id):
        """
        Copy all the course assets from source_course_key to dest_course_key.
        If dest_course already has assets, this removes the previous value.
        It doesn't combine the assets in dest.

        Arguments:
            source_course_key (CourseKey): identifier of course to copy from
            dest_course_key (CourseKey): identifier of course to copy to
        """
        source_assets = self._find_course_assets(source_course_key)
        dest_assets = {'assets': source_assets.asset_md.copy(), 'course_id': str(dest_course_key)}
        self.asset_collection.delete_many({'course_id': str(dest_course_key)})
        # Update the document.
        self.asset_collection.insert_one(dest_assets)

    def set_asset_metadata_attrs(self, asset_key, attr_dict, user_id):  # lint-amnesty, pylint: disable=arguments-differ
        """
        Add/set the given dict of attrs on the asset at the given location. Value can be any type which pymongo accepts.

        Arguments:
            asset_key (AssetKey): asset identifier
            attr_dict (dict): attribute: value pairs to set

        Raises:
            ItemNotFoundError if no such item exists
            AttributeError is attr is one of the build in attrs.
        """
        course_assets, asset_idx = self._find_course_asset(asset_key)
        if asset_idx is None:
            raise ItemNotFoundError(asset_key)

        # Form an AssetMetadata.
        all_assets = course_assets[asset_key.asset_type]
        md = AssetMetadata(asset_key, asset_key.path)
        md.from_storable(all_assets[asset_idx])
        md.update(attr_dict)

        # Generate a Mongo doc from the metadata and update the course asset info.
        all_assets[asset_idx] = md.to_storable()

        self.asset_collection.update_one(
            {'_id': course_assets.doc_id},
            {"$set": {self._make_mongo_asset_key(asset_key.asset_type): all_assets}}
        )

    def delete_asset_metadata(self, asset_key, user_id):
        """
        Internal; deletes a single asset's metadata.

        Arguments:
            asset_key (AssetKey): key containing original asset filename

        Returns:
            Number of asset metadata entries deleted (0 or 1)
        """
        course_assets, asset_idx = self._find_course_asset(asset_key)
        if asset_idx is None:
            return 0

        all_asset_info = course_assets[asset_key.asset_type]
        all_asset_info.pop(asset_idx)

        # Update the document.
        self.asset_collection.update_one(
            {'_id': course_assets.doc_id},
            {'$set': {self._make_mongo_asset_key(asset_key.asset_type): all_asset_info}}
        )
        return 1

    def delete_all_asset_metadata(self, course_key, user_id):  # lint-amnesty, pylint: disable=unused-argument
        """
        Delete all of the assets which use this course_key as an identifier.

        Arguments:
            course_key (CourseKey): course_identifier
        """
        # Using the course_id, find the course asset metadata document.
        # A single document exists per course to store the course asset metadata.
        try:
            course_assets = self._find_course_assets(course_key)
            self.asset_collection.delete_many({'_id': course_assets.doc_id})
        except ItemNotFoundError:
            # When deleting asset metadata, if a course's asset metadata is not present, no big deal.
            pass

    def heartbeat(self):
        """
        Check that the db is reachable.
        """
        try:
            # The ismaster command is cheap and does not require auth.
            self.database.client.admin.command('ismaster')
            return {ModuleStoreEnum.Type.mongo: True}
        except pymongo.errors.ConnectionFailure:
            raise HeartbeatFailure(f"Can't connect to {self.database.name}", 'mongo')  # lint-amnesty, pylint: disable=raise-missing-from

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.

        This method is intended for use by tests and administrative commands, and not
        to be run during server startup.
        """
        # Because we often query for some subset of the id, we define this index:
        create_collection_index(
            self.collection,
            [
                ('_id.tag', pymongo.ASCENDING),
                ('_id.org', pymongo.ASCENDING),
                ('_id.course', pymongo.ASCENDING),
                ('_id.category', pymongo.ASCENDING),
                ('_id.name', pymongo.ASCENDING),
                ('_id.revision', pymongo.ASCENDING),
            ],
            background=True
        )

        # Because we often scan for all category='course' regardless of the value of the other fields:
        create_collection_index(self.collection, '_id.category', background=True)

        # Because lms calls get_parent_locations frequently (for path generation):
        create_collection_index(self.collection, 'definition.children', sparse=True, background=True)

        # To allow prioritizing draft vs published material
        create_collection_index(self.collection, '_id.revision', background=True)

    # Some overrides that still need to be implemented by subclasses
    def convert_to_draft(self, location, user_id):
        raise NotImplementedError()

    def delete_item(self, location, user_id, **kwargs):  # lint-amnesty, pylint: disable=arguments-differ
        raise NotImplementedError()

    def has_changes(self, xblock):
        raise NotImplementedError()

    def has_published_version(self, xblock):
        raise NotImplementedError()

    def publish(self, location, user_id):
        raise NotImplementedError()

    def revert_to_published(self, location, user_id):
        raise NotImplementedError()

    def unpublish(self, location, user_id):
        raise NotImplementedError()
