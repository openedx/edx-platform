"""
Modulestore backed by Mongodb.

Stores individual XModules as single documents with the following
structure:

{
    '_id': <location.as_dict>,
    'metadata': <dict containing all Scope.settings fields>
    'definition': <dict containing all Scope.content fields>
    'definition.children': <list of all child location.to_deprecated_string()s>
}
"""

import pymongo
import sys
import logging
import copy
import re
from uuid import uuid4

from bson.son import SON
from fs.osfs import OSFS
from path import path
from datetime import datetime
from pytz import UTC
from contracts import contract, new_contract

from importlib import import_module
from xmodule.errortracker import null_error_tracker, exc_info_to_str
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.error_module import ErrorDescriptor
from xblock.runtime import KvsFieldData
from xblock.exceptions import InvalidScopeError
from xblock.fields import Scope, ScopeIds, Reference, ReferenceList, ReferenceValueDict

from xmodule.modulestore import ModuleStoreWriteBase, ModuleStoreEnum, BulkOperationsMixin, BulkOpsRecord
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished, DIRECT_ONLY_CATEGORIES
from opaque_keys.edx.locations import Location
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateCourseError, ReferentialIntegrityError
from xmodule.modulestore.inheritance import InheritanceMixin, inherit_metadata, InheritanceKeyValueStore
from xblock.core import XBlock
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import UsageKey, CourseKey, AssetKey
from xmodule.exceptions import HeartbeatFailure
from xmodule.modulestore.edit_info import EditInfoRuntimeMixin
from xmodule.assetstore import AssetMetadata, AssetThumbnailMetadata

log = logging.getLogger(__name__)

new_contract('CourseKey', CourseKey)
new_contract('AssetKey', AssetKey)
new_contract('AssetMetadata', AssetMetadata)
new_contract('AssetThumbnailMetadata', AssetThumbnailMetadata)

# sort order that returns DRAFT items first
SORT_REVISION_FAVOR_DRAFT = ('_id.revision', pymongo.DESCENDING)

# sort order that returns PUBLISHED items first
SORT_REVISION_FAVOR_PUBLISHED = ('_id.revision', pymongo.ASCENDING)

BLOCK_TYPES_WITH_CHILDREN = list(set(
    name for name, class_ in XBlock.load_classes() if getattr(class_, 'has_children', False)
))

# Allow us to call _from_deprecated_(son|string) throughout the file
# pylint: disable=protected-access


class MongoRevisionKey(object):
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
    pass


class MongoKeyValueStore(InheritanceKeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """
    def __init__(self, data, children, metadata):
        super(MongoKeyValueStore, self).__init__()
        if not isinstance(data, dict):
            self._data = {'data': data}
        else:
            self._data = data
        self._children = children
        self._metadata = metadata

    def get(self, key):
        if key.scope == Scope.children:
            return self._children
        elif key.scope == Scope.parent:
            return None
        elif key.scope == Scope.settings:
            return self._metadata[key.field_name]
        elif key.scope == Scope.content:
            return self._data[key.field_name]
        else:
            raise InvalidScopeError(key)

    def set(self, key, value):
        if key.scope == Scope.children:
            self._children = value
        elif key.scope == Scope.settings:
            self._metadata[key.field_name] = value
        elif key.scope == Scope.content:
            self._data[key.field_name] = value
        else:
            raise InvalidScopeError(key)

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
            raise InvalidScopeError(key)

    def has(self, key):
        if key.scope in (Scope.children, Scope.parent):
            return True
        elif key.scope == Scope.settings:
            return key.field_name in self._metadata
        elif key.scope == Scope.content:
            return key.field_name in self._data
        else:
            return False


class CachingDescriptorSystem(MakoDescriptorSystem, EditInfoRuntimeMixin):
    """
    A system that has a cache of module json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data
    """
    def __init__(self, modulestore, course_key, module_data, default_class, cached_metadata, **kwargs):
        """
        modulestore: the module store that can be used to retrieve additional modules

        course_key: the course for which everything in this runtime will be relative

        module_data: a dict mapping Location -> json that was cached from the
            underlying modulestore

        default_class: The default_class to use when loading an
            XModuleDescriptor from the module_data

        cached_metadata: the cache for handling inheritance computation. internal use only

        resources_fs: a filesystem, as per MakoDescriptorSystem

        error_tracker: a function that logs errors for later display to users

        render_template: a function for rendering templates, as per
            MakoDescriptorSystem
        """
        super(CachingDescriptorSystem, self).__init__(
            field_data=None,
            load_item=self.load_item,
            **kwargs
        )

        self.modulestore = modulestore
        self.module_data = module_data
        self.default_class = default_class
        # cdodge: other Systems have a course_id attribute defined. To keep things consistent, let's
        # define an attribute here as well, even though it's None
        self.course_id = course_key
        self.cached_metadata = cached_metadata

    def load_item(self, location):
        """
        Return an XModule instance for the specified location
        """
        assert isinstance(location, UsageKey)
        json_data = self.module_data.get(location)
        if json_data is None:
            module = self.modulestore.get_item(location)
            if module is not None:
                # update our own cache after going to the DB to get cache miss
                self.module_data.update(module.runtime.module_data)
            return module
        else:
            # load the module and apply the inherited metadata
            try:
                category = json_data['location']['category']
                class_ = self.load_block_type(category)

                definition = json_data.get('definition', {})
                metadata = json_data.get('metadata', {})
                for old_name, new_name in getattr(class_, 'metadata_translations', {}).items():
                    if old_name in metadata:
                        metadata[new_name] = metadata[old_name]
                        del metadata[old_name]

                children = [
                    self._convert_reference_to_key(childloc)
                    for childloc in definition.get('children', [])
                ]
                data = definition.get('data', {})
                if isinstance(data, basestring):
                    data = {'data': data}
                mixed_class = self.mixologist.mix(class_)
                if data:  # empty or None means no work
                    data = self._convert_reference_fields_to_keys(mixed_class, location.course_key, data)
                metadata = self._convert_reference_fields_to_keys(mixed_class, location.course_key, metadata)
                kvs = MongoKeyValueStore(
                    data,
                    children,
                    metadata,
                )

                field_data = KvsFieldData(kvs)
                scope_ids = ScopeIds(None, category, location, location)
                module = self.construct_xblock_from_class(class_, scope_ids, field_data)
                if self.cached_metadata is not None:
                    # parent container pointers don't differentiate between draft and non-draft
                    # so when we do the lookup, we should do so with a non-draft location
                    non_draft_loc = as_published(location)

                    # Convert the serialized fields values in self.cached_metadata
                    # to python values
                    metadata_to_inherit = self.cached_metadata.get(unicode(non_draft_loc), {})
                    inherit_metadata(module, metadata_to_inherit)

                module._edit_info = json_data.get('edit_info')

                # migrate published_by and published_on if edit_info isn't present
                if module._edit_info is None:
                    module._edit_info = {}
                    raw_metadata = json_data.get('metadata', {})
                    # published_on was previously stored as a list of time components instead of a datetime
                    if raw_metadata.get('published_date'):
                        module._edit_info['published_date'] = datetime(*raw_metadata.get('published_date')[0:6]).replace(tzinfo=UTC)
                    module._edit_info['published_by'] = raw_metadata.get('published_by')

                # decache any computed pending field settings
                module.save()
                return module
            except:
                log.warning("Failed to load descriptor from %s", json_data, exc_info=True)
                return ErrorDescriptor.from_json(
                    json_data,
                    self,
                    location,
                    error_msg=exc_info_to_str(sys.exc_info())
                )

    def _convert_reference_to_key(self, ref_string):
        """
        Convert a single serialized UsageKey string in a ReferenceField into a UsageKey.
        """
        key = Location.from_string(ref_string)
        return key.replace(run=self.modulestore.fill_in_run(key.course_key).run)

    def __setattr__(self, name, value):
        return super(CachingDescriptorSystem, self).__setattr__(name, value)

    def _convert_reference_fields_to_keys(self, class_, course_key, jsonfields):
        """
        Find all fields of type reference and convert the payload into UsageKeys
        :param class_: the XBlock class
        :param course_key: a CourseKey object for the given course
        :param jsonfields: a dict of the jsonified version of the fields
        """
        result = {}
        for field_name, value in jsonfields.iteritems():
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
                    key: self._convert_reference_to_key(subvalue) for key, subvalue in value.iteritems()
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
    if location.category in DIRECT_ONLY_CATEGORIES:
        return location
    return location.replace(revision=MongoRevisionKey.draft)


def as_published(location):
    """
    Returns the Location that is the published version for `location`
    """
    return location.replace(revision=MongoRevisionKey.published)


class MongoBulkOpsRecord(BulkOpsRecord):
    """
    Tracks whether there've been any writes per course and disables inheritance generation
    """
    def __init__(self):
        super(MongoBulkOpsRecord, self).__init__()
        self.dirty = False


class MongoBulkOpsMixin(BulkOperationsMixin):
    """
    Mongo bulk operation support
    """
    _bulk_ops_record_type = MongoBulkOpsRecord

    def _start_outermost_bulk_operation(self, bulk_ops_record, course_key):
        """
        Prevent updating the meta-data inheritance cache for the given course
        """
        # ensure it starts clean
        bulk_ops_record.dirty = False

    def _end_outermost_bulk_operation(self, bulk_ops_record, course_id):
        """
        Restart updating the meta-data inheritance cache for the given course.
        Refresh the meta-data inheritance cache now since it was temporarily disabled.
        """
        if bulk_ops_record.dirty:
            self.refresh_cached_metadata_inheritance_tree(course_id)
            bulk_ops_record.dirty = False  # brand spanking clean now

    def _is_in_bulk_operation(self, course_id, ignore_case=False):
        """
        Returns whether a bulk operation is in progress for the given course.
        """
        return super(MongoBulkOpsMixin, self)._is_in_bulk_operation(
            course_id.for_branch(None), ignore_case
        )


class MongoModuleStore(ModuleStoreDraftAndPublished, ModuleStoreWriteBase, MongoBulkOpsMixin):
    """
    A Mongodb backed ModuleStore
    """
    # TODO (cpennington): Enable non-filesystem filestores
    # pylint: disable=C0103
    # pylint: disable=W0201
    def __init__(self, contentstore, doc_store_config, fs_root, render_template,
                 default_class=None,
                 error_tracker=null_error_tracker,
                 i18n_service=None,
                 fs_service=None,
                 **kwargs):
        """
        :param doc_store_config: must have a host, db, and collection entries. Other common entries: port, tz_aware.
        """

        super(MongoModuleStore, self).__init__(contentstore=contentstore, **kwargs)

        def do_connection(
            db, collection, host, port=27017, tz_aware=True, user=None, password=None, asset_collection=None, **kwargs
        ):
            """
            Create & open the connection, authenticate, and provide pointers to the collection
            """
            self.database = pymongo.database.Database(
                pymongo.MongoClient(
                    host=host,
                    port=port,
                    tz_aware=tz_aware,
                    document_class=dict,
                    **kwargs
                ),
                db
            )
            self.collection = self.database[collection]

            # Collection which stores asset metadata.
            self.asset_collection = None
            if asset_collection is not None:
                self.asset_collection = self.database[asset_collection]

            if user is not None and password is not None:
                self.database.authenticate(user, password)

        do_connection(**doc_store_config)

        # Force mongo to report errors, at the expense of performance
        self.collection.write_concern = {'w': 1}

        if default_class is not None:
            module_path, _, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_
        else:
            self.default_class = None
        self.fs_root = path(fs_root)
        self.error_tracker = error_tracker
        self.render_template = render_template
        self.i18n_service = i18n_service
        self.fs_service = fs_service

        self._course_run_cache = {}

    def close_connections(self):
        """
        Closes any open connections to the underlying database
        """
        self.collection.database.connection.close()

    def mongo_wire_version(self):
        """
        Returns the wire version for mongo. Only used to unit tests which instrument the connection.
        """
        self.database.connection._ensure_connected()
        return self.database.connection.max_wire_version

    def _drop_database(self):
        """
        A destructive operation to drop the underlying database and close all connections.
        Intended to be used by test code for cleanup.
        """
        # drop the assets
        super(MongoModuleStore, self)._drop_database()

        connection = self.collection.database.connection
        connection.drop_database(self.collection.database)
        connection.close()

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
        if location.category in DIRECT_ONLY_CATEGORIES:
            return location.replace(revision=MongoRevisionKey.published)
        if self.get_branch_setting() == ModuleStoreEnum.Branch.draft_preferred:
            return location.replace(revision=MongoRevisionKey.draft)
        return location.replace(revision=MongoRevisionKey.published)

    def _compute_metadata_inheritance_tree(self, course_id):
        '''
        TODO (cdodge) This method can be deleted when the 'split module store' work has been completed
        '''
        # get all collections in the course, this query should not return any leaf nodes
        # note this is a bit ugly as when we add new categories of containers, we have to add it here

        course_id = self.fill_in_run(course_id)
        query = SON([
            ('_id.tag', 'i4x'),
            ('_id.org', course_id.org),
            ('_id.course', course_id.course),
            ('_id.category', {'$in': BLOCK_TYPES_WITH_CHILDREN})
        ])
        # we just want the Location, children, and inheritable metadata
        record_filter = {'_id': 1, 'definition.children': 1}

        # just get the inheritable metadata since that is all we need for the computation
        # this minimizes both data pushed over the wire
        for field_name in InheritanceMixin.fields:
            record_filter['metadata.{0}'.format(field_name)] = 1

        # call out to the DB
        resultset = self.collection.find(query, record_filter)

        # it's ok to keep these as deprecated strings b/c the overall cache is indexed by course_key and this
        # is a dictionary relative to that course
        results_by_url = {}
        root = None

        # now go through the results and order them by the location url
        for result in resultset:
            # manually pick it apart b/c the db has tag and we want as_published revision regardless
            location = as_published(Location._from_deprecated_son(result['_id'], course_id.run))

            location_url = unicode(location)
            if location_url in results_by_url:
                # found either draft or live to complement the other revision
                existing_children = results_by_url[location_url].get('definition', {}).get('children', [])
                additional_children = result.get('definition', {}).get('children', [])
                total_children = existing_children + additional_children
                # use set to get rid of duplicates. We don't care about order; so, it shouldn't matter.
                results_by_url[location_url].setdefault('definition', {})['children'] = set(total_children)
            else:
                results_by_url[location_url] = result
            if location.category == 'course':
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
                    metadata_to_inherit[child] = my_metadata

        if root is not None:
            _compute_inherited_metadata(root)

        return metadata_to_inherit

    def _get_cached_metadata_inheritance_tree(self, course_id, force_refresh=False):
        '''
        Compute the metadata inheritance for the course.
        '''
        tree = {}

        course_id = self.fill_in_run(course_id)
        if not force_refresh:
            # see if we are first in the request cache (if present)
            if self.request_cache is not None and unicode(course_id) in self.request_cache.data.get('metadata_inheritance', {}):
                return self.request_cache.data['metadata_inheritance'][unicode(course_id)]

            # then look in any caching subsystem (e.g. memcached)
            if self.metadata_inheritance_cache_subsystem is not None:
                tree = self.metadata_inheritance_cache_subsystem.get(unicode(course_id), {})
            else:
                logging.warning(
                    'Running MongoModuleStore without a metadata_inheritance_cache_subsystem. This is \
                    OK in localdev and testing environment. Not OK in production.'
                )

        if not tree:
            # if not in subsystem, or we are on force refresh, then we have to compute
            tree = self._compute_metadata_inheritance_tree(course_id)

            # now write out computed tree to caching subsystem (e.g. memcached), if available
            if self.metadata_inheritance_cache_subsystem is not None:
                self.metadata_inheritance_cache_subsystem.set(unicode(course_id), tree)

        # now populate a request_cache, if available. NOTE, we are outside of the
        # scope of the above if: statement so that after a memcache hit, it'll get
        # put into the request_cache
        if self.request_cache is not None:
            # we can't assume the 'metadatat_inheritance' part of the request cache dict has been
            # defined
            if 'metadata_inheritance' not in self.request_cache.data:
                self.request_cache.data['metadata_inheritance'] = {}
            self.request_cache.data['metadata_inheritance'][unicode(course_id)] = tree

        return tree

    def refresh_cached_metadata_inheritance_tree(self, course_id, runtime=None):
        """
        Refresh the cached metadata inheritance tree for the org/course combination
        for location

        If given a runtime, it replaces the cached_metadata in that runtime. NOTE: failure to provide
        a runtime may mean that some objects report old values for inherited data.
        """
        course_id = course_id.for_branch(None)
        if not self._is_in_bulk_operation(course_id):
            # below is done for side effects when runtime is None
            cached_metadata = self._get_cached_metadata_inheritance_tree(course_id, force_refresh=True)
            if runtime:
                runtime.cached_metadata = cached_metadata

    def _clean_item_data(self, item):
        """
        Renames the '_id' field in item to 'location'
        """
        item['location'] = item['_id']
        del item['_id']

    def _query_children_for_cache_children(self, course_key, items):
        """
        Generate a pymongo in query for finding the items and return the payloads
        """
        # first get non-draft in a round-trip
        query = {
            '_id': {'$in': [
                course_key.make_usage_key_from_deprecated_string(item).to_deprecated_son() for item in items
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
        while to_process and depth is None or depth >= 0:
            children = []
            for item in to_process:
                self._clean_item_data(item)
                children.extend(item.get('definition', {}).get('children', []))
                data[Location._from_deprecated_son(item['location'], course_key.run)] = item

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

    def _load_item(self, course_key, item, data_cache, apply_cached_metadata=True):
        """
        Load an XModuleDescriptor from item, using the children stored in data_cache
        """
        course_key = self.fill_in_run(course_key)
        location = Location._from_deprecated_son(item['location'], course_key.run)
        data_dir = getattr(item, 'data_dir', location.course)
        root = self.fs_root / data_dir

        root.makedirs_p()  # create directory if it doesn't exist

        resource_fs = OSFS(root)

        cached_metadata = {}
        if apply_cached_metadata:
            cached_metadata = self._get_cached_metadata_inheritance_tree(course_key)

        services = {}
        if self.i18n_service:
            services["i18n"] = self.i18n_service

        if self.fs_service:
            services["fs"] = self.fs_service

        system = CachingDescriptorSystem(
            modulestore=self,
            course_key=course_key,
            module_data=data_cache,
            default_class=self.default_class,
            resources_fs=resource_fs,
            error_tracker=self.error_tracker,
            render_template=self.render_template,
            cached_metadata=cached_metadata,
            mixins=self.xblock_mixins,
            select=self.xblock_select,
            services=services,
        )
        return system.load_item(location)

    def _load_items(self, course_key, items, depth=0):
        """
        Load a list of xmodules from the data in items, with children cached up
        to specified depth
        """
        course_key = self.fill_in_run(course_key)
        data_cache = self._cache_children(course_key, items, depth)

        # if we are loading a course object, if we're not prefetching children (depth != 0) then don't
        # bother with the metadata inheritance
        return [
            self._load_item(
                course_key, item, data_cache,
                apply_cached_metadata=(item['location']['category'] != 'course' or depth != 0)
            )
            for item in items
        ]

    def get_courses(self, **kwargs):
        '''
        Returns a list of course descriptors.
        '''
        base_list = sum(
            [
                self._load_items(
                    SlashSeparatedCourseKey(course['_id']['org'], course['_id']['course'], course['_id']['name']),
                    [course]
                )
                for course
                # I tried to add '$and': [{'_id.org': {'$ne': 'edx'}}, {'_id.course': {'$ne': 'templates'}}]
                # but it didn't do the right thing (it filtered all edx and all templates out)
                in self.collection.find({'_id.category': 'course'})
                if not (  # TODO kill this
                    course['_id']['org'] == 'edx' and
                    course['_id']['course'] == 'templates'
                )
            ],
            []
        )
        return [course for course in base_list if not isinstance(course, ErrorDescriptor)]

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

    def get_course(self, course_key, depth=0, **kwargs):
        """
        Get the course with the given courseid (org/course/run)
        """
        assert(isinstance(course_key, CourseKey))
        course_key = self.fill_in_run(course_key)
        location = course_key.make_usage_key('course', course_key.run)
        try:
            return self.get_item(location, depth=depth)
        except ItemNotFoundError:
            return None

    def has_course(self, course_key, ignore_case=False, **kwargs):
        """
        Returns the course_id of the course if it was found, else None
        Note: we return the course_id instead of a boolean here since the found course may have
           a different id than the given course_id when ignore_case is True.

        If ignore_case is True, do a case insensitive search,
        otherwise, do a case sensitive search
        """
        assert(isinstance(course_key, CourseKey))
        course_key = self.fill_in_run(course_key)
        location = course_key.make_usage_key('course', course_key.run)
        if ignore_case:
            course_query = location.to_deprecated_son('_id.')
            for key in course_query.iterkeys():
                if isinstance(course_query[key], basestring):
                    course_query[key] = re.compile(r"(?i)^{}$".format(course_query[key]))
        else:
            course_query = {'_id': location.to_deprecated_son()}
        course = self.collection.find_one(course_query, fields={'_id': True})
        if course:
            return SlashSeparatedCourseKey(course['_id']['org'], course['_id']['course'], course['_id']['name'])
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

    def get_item(self, usage_key, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        usage_key: a :class:`.UsageKey` instance
        depth (int): An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of
            calls to get_children() to cache. None indicates to cache all descendents.
        """
        item = self._find_one(usage_key)
        module = self._load_items(usage_key.course_key, [item], depth)[0]
        return module

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

    def get_items(
            self,
            course_id,
            settings=None,
            content=None,
            key_revision=MongoRevisionKey.published,
            qualifiers=None,
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
        """
        qualifiers = qualifiers.copy() if qualifiers else {}  # copy the qualifiers (destructively manipulated here)
        query = self._course_key_to_son(course_id)
        query['_id.revision'] = key_revision
        for field in ['category', 'name']:
            if field in qualifiers:
                query['_id.' + field] = qualifiers.pop(field)

        for key, value in (settings or {}).iteritems():
            query['metadata.' + key] = value
        for key, value in (content or {}).iteritems():
            query['definition.data.' + key] = value
        if 'children' in qualifiers:
            query['definition.children'] = qualifiers.pop('children')

        query.update(qualifiers)
        items = self.collection.find(
            query,
            sort=[SORT_REVISION_FAVOR_DRAFT],
        )

        modules = self._load_items(course_id, list(items))
        return modules

    def create_course(self, org, course, run, user_id, fields=None, **kwargs):
        """
        Creates and returns the course.

        Args:
            org (str): the organization that owns the course
            course (str): the name of the course
            run (str): the name of the run
            user_id: id of the user creating the course
            fields (dict): Fields to set on the course at initialization
            kwargs: Any optional arguments understood by a subset of modulestores to customize instantiation

        Returns: a CourseDescriptor

        Raises:
            InvalidLocationError: If a course with the same org, course, and run already exists
        """
        course_id = SlashSeparatedCourseKey(org, course, run)

        # Check if a course with this org/course has been defined before (case-insensitive)
        course_search_location = SON([
            ('_id.tag', 'i4x'),
            ('_id.org', re.compile(u'^{}$'.format(course_id.org), re.IGNORECASE)),
            ('_id.course', re.compile(u'^{}$'.format(course_id.course), re.IGNORECASE)),
            ('_id.category', 'course'),
        ])
        courses = self.collection.find(course_search_location, fields=('_id'))
        if courses.count() > 0:
            raise DuplicateCourseError(course_id, courses[0]['_id'])

        xblock = self.create_item(user_id, course_id, 'course', course_id.run, fields=fields, **kwargs)

        # create any other necessary things as a side effect
        super(MongoModuleStore, self).create_course(
            org, course, run, user_id, runtime=xblock.runtime, **kwargs
        )

        return xblock

    def create_xblock(
        self, runtime, course_key, block_type, block_id=None, fields=None,
        metadata=None, definition_data=None, **kwargs
    ):
        """
        Create the new xblock but don't save it. Returns the new module.

        :param runtime: if you already have an xblock from the course, the xblock.runtime value
        :param fields: a dictionary of field names and values for the new xmodule
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
                block_id = u'{}_{}'.format(block_type, uuid4().hex[:5])

        if runtime is None:
            services = {}
            if self.i18n_service:
                services["i18n"] = self.i18n_service

            if self.fs_service:
                services["fs"] = self.fs_service

            runtime = CachingDescriptorSystem(
                modulestore=self,
                module_data={},
                course_key=course_key,
                default_class=self.default_class,
                resources_fs=None,
                error_tracker=self.error_tracker,
                render_template=self.render_template,
                cached_metadata={},
                mixins=self.xblock_mixins,
                select=self.xblock_select,
                services=services,
            )
        xblock_class = runtime.load_block_type(block_type)
        location = course_key.make_usage_key(block_type, block_id)
        dbmodel = self._create_new_field_data(block_type, location, definition_data, metadata)
        xmodule = runtime.construct_xblock_from_class(
            xblock_class,
            # We're loading a descriptor, so student_id is meaningless
            # We also don't have separate notions of definition and usage ids yet,
            # so we use the location for both.
            ScopeIds(None, block_type, location, location),
            dbmodel,
        )
        if fields is not None:
            for key, value in fields.iteritems():
                setattr(xmodule, key, value)
        # decache any pending field settings from init
        xmodule.save()
        return xmodule

    def create_item(self, user_id, course_key, block_type, block_id=None, **kwargs):
        """
        Creates and saves a new item in a course.

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
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
                block_id = u'{}_{}'.format(block_type, uuid4().hex[:5])

        runtime = kwargs.pop('runtime', None)
        xblock = self.create_xblock(runtime, course_key, block_type, block_id, **kwargs)
        xblock = self.update_item(xblock, user_id, allow_not_found=True)

        return xblock

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, **kwargs):
        """
        Creates and saves a new xblock that as a child of the specified block

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
            parent_usage_key: a :class:`~opaque_key.edx.UsageKey` identifing the
                block that this item should be parented under
            block_type: The typo of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
        """
        xblock = self.create_item(user_id, parent_usage_key.course_key, block_type, block_id=block_id, **kwargs)
        # attach to parent if given
        if 'detached' not in xblock._class_tags:
            parent = self.get_item(parent_usage_key)
            parent.children.append(xblock.location)
            self.update_item(parent, user_id)

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
        for a given Xmodule, return the course that it belongs to
        Also we have to assert that this module maps to only one course item - it'll throw an
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
        result = self.collection.update(
            {'_id': location.to_deprecated_son()},
            {'$set': update},
            multi=False,
            upsert=allow_not_found,
            w=1,  # wait until primary commits
        )
        if result['n'] == 0:
            raise ItemNotFoundError(location)

    def _update_ancestors(self, location, update):
        """
        Recursively applies update to all the ancestors of location
        """
        parent = self._get_raw_parent_location(as_published(location), ModuleStoreEnum.RevisionOption.draft_preferred)
        if parent:
            self._update_single_item(parent, update)
            self._update_ancestors(parent, update)

    def update_item(self, xblock, user_id, allow_not_found=False, force=False, isPublish=False,
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
            self._update_single_item(xblock.scope_ids.usage_id, payload, allow_not_found=allow_not_found)

            # update subtree edited info for ancestors
            # don't update the subtree info for descendants of the publish root for efficiency
            if (
                (not isPublish or (isPublish and is_publish_root)) and
                not self._is_in_bulk_operation(xblock.location.course_key)
            ):
                ancestor_payload = {
                    'edit_info.subtree_edited_on': now,
                    'edit_info.subtree_edited_by': user_id
                }
                self._update_ancestors(xblock.scope_ids.usage_id, ancestor_payload)

            # update the edit info of the instantiated xblock
            xblock._edit_info = payload['edit_info']

            # recompute (and update) the metadata inheritance tree which is cached
            self.refresh_cached_metadata_inheritance_tree(xblock.scope_ids.usage_id.course_key, xblock.runtime)
            # fire signal that we've written to DB
        except ItemNotFoundError:
            if not allow_not_found:
                raise
            elif not self.has_course(xblock.location.course_key):
                raise ItemNotFoundError(xblock.location.course_key)

        return xblock

    def _serialize_scope(self, xblock, scope):
        """
        Find all fields of type reference and convert the payload from UsageKeys to deprecated strings
        :param xblock: the XBlock class
        :param jsonfields: a dict of the jsonified version of the fields
        """
        jsonfields = {}
        for field_name, field in xblock.fields.iteritems():
            if (field.scope == scope and field.is_set_on(xblock)):
                if isinstance(field, Reference):
                    jsonfields[field_name] = unicode(field.read_from(xblock))
                elif isinstance(field, ReferenceList):
                    jsonfields[field_name] = [
                        unicode(ele) for ele in field.read_from(xblock)
                    ]
                elif isinstance(field, ReferenceValueDict):
                    jsonfields[field_name] = {
                        key: unicode(subvalue) for key, subvalue in field.read_from(xblock).iteritems()
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
            parent_loc = Location._from_deprecated_son(parent['_id'], location.course_key.run)

            # travel up the tree for orphan validation
            ancestor_loc = parent_loc
            while ancestor_loc is not None:
                current_loc = ancestor_loc
                ancestor_loc = self._get_raw_parent_location(current_loc, revision)
                if ancestor_loc is None:
                    bulk_record.dirty = True
                    # The parent is an orphan, so remove all the children including
                    # the location whose parent we are looking for from orphan parent
                    self.collection.update(
                        {'_id': parent_loc.to_deprecated_son()},
                        {'$set': {'definition.children': []}},
                        multi=False,
                        upsert=True,
                    )
                elif ancestor_loc.category == 'course':
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
        assert location.revision is None
        assert revision == ModuleStoreEnum.RevisionOption.published_only \
            or revision == ModuleStoreEnum.RevisionOption.draft_preferred

        # create a query with tag, org, course, and the children field set to the given location
        query = self._course_key_to_son(location.course_key)
        query['definition.children'] = unicode(location)

        # if only looking for the PUBLISHED parent, set the revision in the query to None
        if revision == ModuleStoreEnum.RevisionOption.published_only:
            query['_id.revision'] = MongoRevisionKey.published

        # query the collection, sorting by DRAFT first
        parents = self.collection.find(query, {'_id': True}, sort=[SORT_REVISION_FAVOR_DRAFT])

        if parents.count() == 0:
            # no parents were found
            return None

        if revision == ModuleStoreEnum.RevisionOption.published_only:
            if parents.count() > 1:
                non_orphan_parents = self._get_non_orphan_parents(location, parents, revision)
                if len(non_orphan_parents) == 0:
                    # no actual parent found
                    return None

                if len(non_orphan_parents) > 1:
                    # should never have multiple PUBLISHED parents
                    raise ReferentialIntegrityError(
                        u"{} parents claim {}".format(parents.count(), location)
                    )
                else:
                    return non_orphan_parents[0]
            else:
                # return the single PUBLISHED parent
                return Location._from_deprecated_son(parents[0]['_id'], location.course_key.run)
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
                return non_orphan_parents[0]

            found_id = all_parents[0]['_id']
            # don't disclose revision outside modulestore
            return Location._from_deprecated_son(found_id, location.course_key.run)

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
            return as_published(parent)
        return None

    def get_modulestore_type(self, course_key=None):
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
                    unicode(as_published(Location._from_deprecated_son(item['_id'], course_key.run)))
                )
            all_reachable = all_reachable.union(item.get('definition', {}).get('children', []))
        item_locs -= all_reachable
        return [course_key.make_usage_key_from_deprecated_string(item_loc) for item_loc in item_locs]

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
            Location._from_deprecated_son(course['_id'], course['_id']['name']).course_key
            for course in courses
        ]

    def _create_new_field_data(self, _category, _location, definition_data, metadata):
        """
        To instantiate a new xmodule which will be saved later, set up the dbModel and kvs
        """
        kvs = MongoKeyValueStore(
            definition_data,
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
            Asset info for the course
        """
        if self.asset_collection is None:
            return None

        # Using the course_key, find or insert the course asset metadata document.
        # A single document exists per course to store the course asset metadata.
        course_assets = self.asset_collection.find_one(
            {'course_id': unicode(course_key)},
            fields=('course_id', 'storage', 'assets', 'thumbnails')
        )

        if course_assets is None:
            # Not found, so create.
            course_assets = {'course_id': unicode(course_key), 'storage': 'FILLMEIN-TMP', 'assets': [], 'thumbnails': []}
            course_assets['_id'] = self.asset_collection.insert(course_assets)

        return course_assets

    @contract(course_key='CourseKey', asset_metadata='AssetMetadata | AssetThumbnailMetadata')
    def _save_asset_info(self, course_key, asset_metadata, user_id, thumbnail=False):
        """
        Saves the info for a particular course's asset/thumbnail.

        Arguments:
            course_key (CourseKey): course identifier
            asset_metadata (AssetMetadata/AssetThumbnailMetadata): data about the course asset/thumbnail
            thumbnail (bool): True if saving thumbnail metadata, False if saving asset metadata

        Returns:
            True if info save was successful, else False
        """
        if self.asset_collection is None:
            return False

        course_assets, asset_idx = self._find_course_asset(course_key, asset_metadata.asset_id.path, thumbnail)
        info = 'thumbnails' if thumbnail else 'assets'
        all_assets = course_assets[info]

        # Set the edited information for assets only - not thumbnails.
        if not thumbnail:
            asset_metadata.update({'edited_by': user_id, 'edited_on': datetime.now(UTC)})

        # Translate metadata to Mongo format.
        metadata_to_insert = asset_metadata.to_mongo()
        if asset_idx is None:
            # Append new metadata.
            # Future optimization: Insert in order & binary search to retrieve.
            all_assets.append(metadata_to_insert)
        else:
            # Replace existing metadata.
            all_assets[asset_idx] = metadata_to_insert

        # Update the document.
        self.asset_collection.update({'_id': course_assets['_id']}, {'$set': {info: all_assets}})
        return True

    @contract(asset_key='AssetKey', attr_dict=dict)
    def set_asset_metadata_attrs(self, asset_key, attr_dict, user_id):
        """
        Add/set the given dict of attrs on the asset at the given location. Value can be any type which pymongo accepts.

        Arguments:
            asset_key (AssetKey): asset identifier
            attr_dict (dict): attribute: value pairs to set

        Raises:
            ItemNotFoundError if no such item exists
            AttributeError is attr is one of the build in attrs.
        """
        if self.asset_collection is None:
            return

        course_assets, asset_idx = self._find_course_asset(asset_key.course_key, asset_key.path)
        if asset_idx is None:
            raise ItemNotFoundError(asset_key)

        # Form an AssetMetadata.
        all_assets = course_assets['assets']
        md = AssetMetadata(asset_key, asset_key.path)
        md.from_mongo(all_assets[asset_idx])
        md.update(attr_dict)

        # Generate a Mongo doc from the metadata and update the course asset info.
        all_assets[asset_idx] = md.to_mongo()

        self.asset_collection.update({'_id': course_assets['_id']}, {"$set": {'assets': all_assets}})

    @contract(asset_key='AssetKey')
    def _delete_asset_data(self, asset_key, user_id, thumbnail=False):
        """
        Internal; deletes a single asset's metadata -or- thumbnail.

        Arguments:
            asset_key (AssetKey): key containing original asset/thumbnail filename
            thumbnail: True if thumbnail deletion, False if asset metadata deletion

        Returns:
            Number of asset metadata/thumbnail entries deleted (0 or 1)
        """
        if self.asset_collection is None:
            return 0

        course_assets, asset_idx = self._find_course_asset(asset_key.course_key, asset_key.path, get_thumbnail=thumbnail)
        if asset_idx is None:
            return 0

        info = 'thumbnails' if thumbnail else 'assets'

        all_asset_info = course_assets[info]
        all_asset_info.pop(asset_idx)

        # Update the document.
        self.asset_collection.update({'_id': course_assets['_id']}, {'$set': {info: all_asset_info}})
        return 1

    # pylint: disable=unused-argument
    @contract(course_key='CourseKey')
    def delete_all_asset_metadata(self, course_key, user_id):
        """
        Delete all of the assets which use this course_key as an identifier.

        Arguments:
            course_key (CourseKey): course_identifier
        """
        if self.asset_collection is None:
            return

        # Using the course_id, find the course asset metadata document.
        # A single document exists per course to store the course asset metadata.
        course_assets = self._find_course_assets(course_key)
        self.asset_collection.remove(course_assets['_id'])

    def heartbeat(self):
        """
        Check that the db is reachable.
        """
        if self.database.connection.alive():
            return {ModuleStoreEnum.Type.mongo: True}
        else:
            raise HeartbeatFailure("Can't connect to {}".format(self.database.name), 'mongo')

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.

        This method is intended for use by tests and administrative commands, and not
        to be run during server startup.
        """

        # Because we often query for some subset of the id, we define this index:
        self.collection.create_index([
            ('_id.org', pymongo.ASCENDING),
            ('_id.course', pymongo.ASCENDING),
            ('_id.category', pymongo.ASCENDING),
            ('_id.name', pymongo.ASCENDING),
        ])

        # Because we often scan for all category='course' regardless of the value of the other fields:
        self.collection.create_index('_id.category')

        # Because lms calls get_parent_locations frequently (for path generation):
        self.collection.create_index('definition.children', sparse=True)

        # To allow prioritizing draft vs published material
        self.collection.create_index('_id.revision')
