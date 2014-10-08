"""
Provides full versioning CRUD and representation for collections of xblocks (e.g., courses, modules, etc).

Representation:
* course_index: a dictionary:
    ** '_id': a unique id which cannot change,
    ** 'org': the org's id. Only used for searching not identity,
    ** 'course': the course's catalog number
    ** 'run': the course's run id,
    ** 'edited_by': user_id of user who created the original entry,
    ** 'edited_on': the datetime of the original creation,
    ** 'versions': versions_dict: {branch_id: structure_id, ...}
    ** 'search_targets': a dict of search key and value. For example, wiki_slug. Add any fields whose edits
        should change the search targets to SplitMongoModuleStore.SEARCH_TARGET dict
* structure:
    ** '_id': an ObjectId (guid),
    ** 'root': BlockKey (the block_type and block_id of the root block in the 'blocks' dictionary)
    ** 'previous_version': the structure from which this one was derived. For published courses, this
    points to the previously published version of the structure not the draft published to this.
    ** 'original_version': the original structure id in the previous_version relation. Is a pseudo object
    identifier enabling quick determination if 2 structures have any shared history,
    ** 'edited_by': user_id of the user whose change caused the creation of this structure version,
    ** 'edited_on': the datetime for the change causing this creation of this structure version,
    ** 'blocks': dictionary of xblocks in this structure:
        *** BlockKey: dictionary of block settings and children:
            **** 'block_type': the xblock type id
            **** 'definition': the db id of the record containing the content payload for this xblock
            **** 'fields': the Scope.settings and children field values
                ***** 'children': This is stored as a list of (block_type, block_id) pairs
            **** 'edit_info': dictionary:
                ***** 'edited_on': when was this xblock's fields last changed (will be edited_on value of
                update_version structure)
                ***** 'edited_by': user_id for who changed this xblock last (will be edited_by value of
                update_version structure)
                ***** 'update_version': the guid for the structure where this xblock got its current field
                values. This may point to a structure not in this structure's history (e.g., to a draft
                branch from which this version was published.)
                ***** 'previous_version': the guid for the structure which previously changed this xblock
                (will be the previous value of update_version; so, may point to a structure not in this
                structure's history.)
                ***** 'source_version': the guid for the structure was copied/published into this block
* definition: shared content with revision history for xblock content fields
    ** '_id': definition_id (guid),
    ** 'block_type': xblock type id
    ** 'fields': scope.content (and possibly other) field values.
    ** 'edit_info': dictionary:
        *** 'edited_by': user_id whose edit caused this version of the definition,
        *** 'edited_on': datetime of the change causing this version
        *** 'previous_version': the definition_id of the previous version of this definition
        *** 'original_version': definition_id of the root of the previous version relation on this
        definition. Acts as a pseudo-object identifier.
"""
import copy
import threading
import datetime
import logging
from contracts import contract, new_contract
from importlib import import_module
from path import path
from pytz import UTC
from bson.objectid import ObjectId

from xblock.core import XBlock
from xblock.fields import Scope, Reference, ReferenceList, ReferenceValueDict
from xmodule.errortracker import null_error_tracker
from opaque_keys.edx.locator import (
    BlockUsageLocator, DefinitionLocator, CourseLocator, VersionTree,
    LocalId,
)
from xmodule.modulestore.exceptions import InsufficientSpecificationError, VersionConflictError, DuplicateItemError, \
    DuplicateCourseError
from xmodule.modulestore import (
    inheritance, ModuleStoreWriteBase, ModuleStoreEnum, BulkOpsRecord, BulkOperationsMixin
)

from ..exceptions import ItemNotFoundError
from .caching_descriptor_system import CachingDescriptorSystem
from xmodule.modulestore.split_mongo.mongo_connection import MongoConnection, BlockKey
from xmodule.error_module import ErrorDescriptor
from _collections import defaultdict
from types import NoneType


log = logging.getLogger(__name__)

# ==============================================================================
#
# Known issue:
#    Inheritance for cached kvs doesn't work on edits. Use case.
#     1) attribute foo is inheritable
#     2) g.children = [p], p.children = [a]
#     3) g.foo = 1 on load
#     4) if g.foo > 0, if p.foo > 0, if a.foo > 0 all eval True
#     5) p.foo = -1
#     6) g.foo > 0, p.foo <= 0 all eval True BUT
#     7) BUG: a.foo > 0 still evals True but should be False
#     8) reread and everything works right
#     9) p.del(foo), p.foo > 0 is True! works
#    10) BUG: a.foo < 0!
#   Local fix wont' permanently work b/c xblock may cache a.foo...
#
# ==============================================================================

# When blacklists are this, all children should be excluded
EXCLUDE_ALL = '*'


new_contract('BlockUsageLocator', BlockUsageLocator)
new_contract('BlockKey', BlockKey)


class SplitBulkWriteRecord(BulkOpsRecord):
    def __init__(self):
        super(SplitBulkWriteRecord, self).__init__()
        self.initial_index = None
        self.index = None
        self.structures = {}
        self.structures_in_db = set()

    # TODO: This needs to track which branches have actually been modified/versioned,
    # so that copying one branch to another doesn't update the original branch.
    @property
    def dirty_branches(self):
        """
        Return a list of which branch version ids differ from what was stored
        in the database at the beginning of this bulk operation.
        """
        # If no course index has been set, then no branches have changed
        if self.index is None:
            return []

        # If there was no index in the database to start with, then all branches
        # are dirty by definition
        if self.initial_index is None:
            return self.index.get('versions', {}).keys()

        # Return branches whose ids differ between self.index and self.initial_index
        return [
            branch
            for branch, _id
            in self.index.get('versions', {}).items()
            if self.initial_index.get('versions', {}).get(branch) != _id
        ]

    def structure_for_branch(self, branch):
        return self.structures.get(self.index.get('versions', {}).get(branch))

    def set_structure_for_branch(self, branch, structure):
        if self.index is not None:
            self.index.setdefault('versions', {})[branch] = structure['_id']
        self.structures[structure['_id']] = structure

    def __repr__(self):
        return u"SplitBulkWriteRecord<{!r}, {!r}, {!r}, {!r}, {!r}>".format(
            self._active_count,
            self.initial_index,
            self.index,
            self.structures,
            self.structures_in_db,
        )


class SplitBulkWriteMixin(BulkOperationsMixin):
    """
    This implements the :meth:`bulk_operations` modulestore semantics for the :class:`SplitMongoModuleStore`.

    In particular, it implements :meth:`_begin_bulk_operation` and
    :meth:`_end_bulk_operation` to provide the external interface, and then exposes a set of methods
    for interacting with course_indexes and structures that can be used by :class:`SplitMongoModuleStore`.

    Internally, this mixin records the set of all active bulk operations (keyed on the active course),
    and only writes those values to ``self.mongo_connection`` when :meth:`_end_bulk_operation` is called.
    If a bulk write operation isn't active, then the changes are immediately written to the underlying
    mongo_connection.
    """
    _bulk_ops_record_type = SplitBulkWriteRecord

    def _get_bulk_ops_record(self, course_key, ignore_case=False):
        """
        Return the :class:`.SplitBulkWriteRecord` for this course.
        """
        # handle split specific things and defer to super otherwise
        if course_key is None:
            return self._bulk_ops_record_type()

        if not isinstance(course_key, CourseLocator):
            raise TypeError(u'{!r} is not a CourseLocator'.format(course_key))
        # handle version_guid based retrieval locally
        if course_key.org is None or course_key.course is None or course_key.run is None:
            return self._active_bulk_ops.records[
                course_key.replace(org=None, course=None, run=None, branch=None)
            ]

        return super(SplitBulkWriteMixin, self)._get_bulk_ops_record(
            course_key.replace(branch=None, version_guid=None), ignore_case
        )

    def _clear_bulk_ops_record(self, course_key):
        """
        Clear the record for this course
        """
        if not isinstance(course_key, CourseLocator):
            raise TypeError('{!r} is not a CourseLocator'.format(course_key))

        if course_key.org and course_key.course and course_key.run:
            del self._active_bulk_ops.records[course_key.replace(branch=None, version_guid=None)]
        else:
            del self._active_bulk_ops.records[
                course_key.replace(org=None, course=None, run=None, branch=None)
            ]

    def _start_outermost_bulk_operation(self, bulk_write_record, course_key):
        """
        Begin a bulk write operation on course_key.
        """
        bulk_write_record.initial_index = self.db_connection.get_course_index(course_key)
        # Ensure that any edits to the index don't pollute the initial_index
        bulk_write_record.index = copy.deepcopy(bulk_write_record.initial_index)

    def _end_outermost_bulk_operation(self, bulk_write_record, course_key):
        """
        End the active bulk write operation on course_key.
        """
        # If the content is dirty, then update the database
        for _id in bulk_write_record.structures.viewkeys() - bulk_write_record.structures_in_db:
            self.db_connection.upsert_structure(bulk_write_record.structures[_id])

        if bulk_write_record.index is not None and bulk_write_record.index != bulk_write_record.initial_index:
            if bulk_write_record.initial_index is None:
                self.db_connection.insert_course_index(bulk_write_record.index)
            else:
                self.db_connection.update_course_index(bulk_write_record.index, from_index=bulk_write_record.initial_index)

    def get_course_index(self, course_key, ignore_case=False):
        """
        Return the index for course_key.
        """
        if self._is_in_bulk_operation(course_key, ignore_case):
            return self._get_bulk_ops_record(course_key, ignore_case).index
        else:
            return self.db_connection.get_course_index(course_key, ignore_case)

    def insert_course_index(self, course_key, index_entry):
        bulk_write_record = self._get_bulk_ops_record(course_key)
        if bulk_write_record.active:
            bulk_write_record.index = index_entry
        else:
            self.db_connection.insert_course_index(index_entry)

    def update_course_index(self, course_key, updated_index_entry):
        """
        Change the given course's index entry.

        Note, this operation can be dangerous and break running courses.

        Does not return anything useful.
        """
        bulk_write_record = self._get_bulk_ops_record(course_key)
        if bulk_write_record.active:
            bulk_write_record.index = updated_index_entry
        else:
            self.db_connection.update_course_index(updated_index_entry)

    def get_structure(self, course_key, version_guid):
        bulk_write_record = self._get_bulk_ops_record(course_key)
        if bulk_write_record.active:
            structure = bulk_write_record.structures.get(version_guid)

            # The structure hasn't been loaded from the db yet, so load it
            if structure is None:
                structure = self.db_connection.get_structure(version_guid)
                bulk_write_record.structures[version_guid] = structure
                if structure is not None:
                    bulk_write_record.structures_in_db.add(version_guid)

            return structure
        else:
            # cast string to ObjectId if necessary
            version_guid = course_key.as_object_id(version_guid)
            return self.db_connection.get_structure(version_guid)

    def update_structure(self, course_key, structure):
        """
        Update a course structure, respecting the current bulk operation status
        (no data will be written to the database if a bulk operation is active.)
        """
        self._clear_cache(structure['_id'])
        bulk_write_record = self._get_bulk_ops_record(course_key)
        if bulk_write_record.active:
            bulk_write_record.structures[structure['_id']] = structure
        else:
            self.db_connection.upsert_structure(structure)

    def version_structure(self, course_key, structure, user_id):
        """
        Copy the structure and update the history info (edited_by, edited_on, previous_version)
        """
        if course_key.branch is None:
            raise InsufficientSpecificationError(course_key)

        bulk_write_record = self._get_bulk_ops_record(course_key)

        # If we have an active bulk write, and it's already been edited, then just use that structure
        if bulk_write_record.active and course_key.branch in bulk_write_record.dirty_branches:
            return bulk_write_record.structure_for_branch(course_key.branch)

        # Otherwise, make a new structure
        new_structure = copy.deepcopy(structure)
        new_structure['_id'] = ObjectId()
        new_structure['previous_version'] = structure['_id']
        new_structure['edited_by'] = user_id
        new_structure['edited_on'] = datetime.datetime.now(UTC)
        new_structure['schema_version'] = self.SCHEMA_VERSION

        # If we're in a bulk write, update the structure used there, and mark it as dirty
        if bulk_write_record.active:
            bulk_write_record.set_structure_for_branch(course_key.branch, new_structure)

        return new_structure

    def version_block(self, block_info, user_id, update_version):
        """
        Update the block_info dictionary based on it having been edited
        """
        if block_info['edit_info'].get('update_version') == update_version:
            return

        block_info['edit_info'] = {
            'edited_on': datetime.datetime.now(UTC),
            'edited_by': user_id,
            'previous_version': block_info['edit_info']['update_version'],
            'update_version': update_version,
        }

    def find_matching_course_indexes(self, branch=None, search_targets=None):
        """
        Find the course_indexes which have the specified branch and search_targets.
        """
        indexes = self.db_connection.find_matching_course_indexes(branch, search_targets)

        for _, record in self._active_records:
            if branch and branch not in record.index.get('versions', {}):
                continue

            if search_targets:
                if any(
                    'search_targets' not in record.index or
                    field not in record.index['search_targets'] or
                    record.index['search_targets'][field] != value
                    for field, value in search_targets.iteritems()
                ):
                    continue

            indexes.append(record.index)

        return indexes

    def find_structures_by_id(self, ids):
        """
        Return all structures that specified in ``ids``.

        If a structure with the same id is in both the cache and the database,
        the cached version will be preferred.

        Arguments:
            ids (list): A list of structure ids
        """
        structures = []
        ids = set(ids)

        for _, record in self._active_records:
            for structure in record.structures.values():
                structure_id = structure.get('_id')
                if structure_id in ids:
                    ids.remove(structure_id)
                    structures.append(structure)

        structures.extend(self.db_connection.find_structures_by_id(list(ids)))
        return structures

    def find_structures_derived_from(self, ids):
        """
        Return all structures that were immediately derived from a structure listed in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        found_structure_ids = set()
        structures = []

        for _, record in self._active_records:
            for structure in record.structures.values():
                if structure.get('previous_version') in ids:
                    structures.append(structure)
                    if '_id' in structure:
                        found_structure_ids.add(structure['_id'])

        structures.extend(
            structure
            for structure in self.db_connection.find_structures_derived_from(ids)
            if structure['_id'] not in found_structure_ids
        )
        return structures

    def find_ancestor_structures(self, original_version, block_key):
        """
        Find all structures that originated from ``original_version`` that contain ``block_key``.

        Any structure found in the cache will be preferred to a structure with the same id from the database.

        Arguments:
            original_version (str or ObjectID): The id of a structure
            block_key (BlockKey): The id of the block in question
        """
        found_structure_ids = set()
        structures = []

        for _, record in self._active_records:
            for structure in record.structures.values():
                if 'original_version' not in structure:
                    continue

                if structure['original_version'] != original_version:
                    continue

                if block_key not in structure.get('blocks', {}):
                    continue

                if 'update_version' not in structure['blocks'][block_key].get('edit_info', {}):
                    continue

                structures.append(structure)
                found_structure_ids.add(structure['_id'])

        structures.extend(
            structure
            for structure in self.db_connection.find_ancestor_structures(original_version, block_key)
            if structure['_id'] not in found_structure_ids
        )
        return structures


class SplitMongoModuleStore(SplitBulkWriteMixin, ModuleStoreWriteBase):
    """
    A Mongodb backed ModuleStore supporting versions, inheritance,
    and sharing.
    """

    SCHEMA_VERSION = 1
    # a list of field names to store in course index search_targets. Note, this will
    # only record one value per key. If branches disagree, the last one set wins.
    # It won't recompute the value on operations such as update_course_index (e.g., to revert to a prev
    # version) but those functions will have an optional arg for setting these.
    SEARCH_TARGET_DICT = ['wiki_slug']

    def __init__(self, contentstore, doc_store_config, fs_root, render_template,
                 default_class=None,
                 error_tracker=null_error_tracker,
                 i18n_service=None, fs_service=None,
                 services=None, **kwargs):
        """
        :param doc_store_config: must have a host, db, and collection entries. Other common entries: port, tz_aware.
        """

        super(SplitMongoModuleStore, self).__init__(contentstore, **kwargs)

        self.db_connection = MongoConnection(**doc_store_config)
        self.db = self.db_connection.database

        # Code review question: How should I expire entries?
        # _add_cache could use a lru mechanism to control the cache size?
        self.thread_cache = threading.local()

        if default_class is not None:
            module_path, __, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_
        else:
            self.default_class = None
        self.fs_root = path(fs_root)
        self.error_tracker = error_tracker
        self.render_template = render_template
        self.services = services or {}
        if i18n_service is not None:
            self.services["i18n"] = i18n_service

        if fs_service is not None:
            self.services["fs"] = fs_service

    def close_connections(self):
        """
        Closes any open connections to the underlying databases
        """
        self.db.connection.close()

    def _drop_database(self):
        """
        A destructive operation to drop the underlying database and close all connections.
        Intended to be used by test code for cleanup.
        """
        # drop the assets
        super(SplitMongoModuleStore, self)._drop_database()

        connection = self.db.connection
        connection.drop_database(self.db.name)
        connection.close()

    def cache_items(self, system, base_block_ids, course_key, depth=0, lazy=True):
        '''
        Handles caching of items once inheritance and any other one time
        per course per fetch operations are done.

        Arguments:
            system: a CachingDescriptorSystem
            base_block_ids: list of BlockIds to fetch
            course_key: the destination course providing the context
            depth: how deep below these to prefetch
            lazy: whether to fetch definitions or use placeholders
        '''
        with self.bulk_operations(course_key):
            new_module_data = {}
            for block_id in base_block_ids:
                new_module_data = self.descendants(
                    system.course_entry['structure']['blocks'],
                    block_id,
                    depth,
                    new_module_data
                )

            if not lazy:
                # Load all descendants by id
                descendent_definitions = self.db_connection.find_matching_definitions({
                    '_id': {'$in': [block['definition']
                                    for block in new_module_data.itervalues()]}})
                # turn into a map
                definitions = {definition['_id']: definition
                               for definition in descendent_definitions}

                for block in new_module_data.itervalues():
                    if block['definition'] in definitions:
                        converted_fields = self.convert_references_to_keys(
                            course_key, system.load_block_type(block['block_type']),
                            definitions[block['definition']].get('fields'),
                            system.course_entry['structure']['blocks'],
                        )
                        block['fields'].update(converted_fields)
                        block['definition_loaded'] = True

            system.module_data.update(new_module_data)
            return system.module_data

    def _load_items(self, course_entry, block_keys, depth=0, lazy=True, **kwargs):
        '''
        Load & cache the given blocks from the course. Prefetch down to the
        given depth. Load the definitions into each block if lazy is False;
        otherwise, use the lazy definition placeholder.
        '''
        runtime = self._get_cache(course_entry['structure']['_id'])
        if runtime is None:
            runtime = self.create_runtime(course_entry, lazy)
            self._add_cache(course_entry['structure']['_id'], runtime)
            course_key = CourseLocator(
                version_guid=course_entry['structure']['_id'],
                org=course_entry.get('org'),
                course=course_entry.get('course'),
                run=course_entry.get('run'),
                branch=course_entry.get('branch'),
            )
            self.cache_items(runtime, block_keys, course_key, depth, lazy)
        return [runtime.load_item(block_key, course_entry, **kwargs) for block_key in block_keys]

    def _get_cache(self, course_version_guid):
        """
        Find the descriptor cache for this course if it exists
        :param course_version_guid:
        """
        if not hasattr(self.thread_cache, 'course_cache'):
            self.thread_cache.course_cache = {}
        system = self.thread_cache.course_cache
        return system.get(course_version_guid)

    def _add_cache(self, course_version_guid, system):
        """
        Save this cache for subsequent access
        :param course_version_guid:
        :param system:
        """
        if not hasattr(self.thread_cache, 'course_cache'):
            self.thread_cache.course_cache = {}
        self.thread_cache.course_cache[course_version_guid] = system
        return system

    def _clear_cache(self, course_version_guid=None):
        """
        Should only be used by testing or something which implements transactional boundary semantics.
        :param course_version_guid: if provided, clear only this entry
        """
        if course_version_guid:
            if not hasattr(self.thread_cache, 'course_cache'):
                self.thread_cache.course_cache = {}
            try:
                del self.thread_cache.course_cache[course_version_guid]
            except KeyError:
                pass
        else:
            self.thread_cache.course_cache = {}

    def _lookup_course(self, course_key):
        '''
        Decode the locator into the right series of db access. Does not
        return the CourseDescriptor! It returns the actual db json from
        structures.

        Semantics: if course id and branch given, then it will get that branch. If
        also give a version_guid, it will see if the current head of that branch == that guid. If not
        it raises VersionConflictError (the version now differs from what it was when you got your
        reference)

        :param course_key: any subclass of CourseLocator
        '''
        if course_key.org and course_key.course and course_key.run:
            if course_key.branch is None:
                raise InsufficientSpecificationError(course_key)

            # use the course id
            index = self.get_course_index(course_key)

            if index is None:
                raise ItemNotFoundError(course_key)
            if course_key.branch not in index['versions']:
                raise ItemNotFoundError(course_key)

            version_guid = index['versions'][course_key.branch]

            if course_key.version_guid is not None and version_guid != course_key.version_guid:
                # This may be a bit too touchy but it's hard to infer intent
                raise VersionConflictError(course_key, version_guid)

        elif course_key.version_guid is None:
            raise InsufficientSpecificationError(course_key)
        else:
            # TODO should this raise an exception if branch was provided?
            version_guid = course_key.version_guid

        entry = self.get_structure(course_key, version_guid)
        if entry is None:
            raise ItemNotFoundError('Structure: {}'.format(version_guid))

        # b/c more than one course can use same structure, the 'org', 'course',
        # 'run', and 'branch' are not intrinsic to structure
        # and the one assoc'd w/ it by another fetch may not be the one relevant to this fetch; so,
        # add it in the envelope for the structure.
        envelope = {
            'org': course_key.org,
            'course': course_key.course,
            'run': course_key.run,
            'branch': course_key.branch,
            'structure': entry,
        }
        return envelope

    def get_courses(self, branch, **kwargs):
        '''
        Returns a list of course descriptors matching any given qualifiers.

        qualifiers should be a dict of keywords matching the db fields or any
        legal query for mongo to use against the active_versions collection.

        Note, this is to find the current head of the named branch type.
        To get specific versions via guid use get_course.

        :param branch: the branch for which to return courses.
        '''
        matching_indexes = self.find_matching_course_indexes(branch)

        # collect ids and then query for those
        version_guids = []
        id_version_map = {}
        for course_index in matching_indexes:
            version_guid = course_index['versions'][branch]
            version_guids.append(version_guid)
            id_version_map[version_guid] = course_index

        if not version_guids:
            return []

        matching_structures = self.find_structures_by_id(version_guids)

        # get the blocks for each course index (s/b the root)
        result = []
        for entry in matching_structures:
            course_info = id_version_map[entry['_id']]
            envelope = {
                'org': course_info['org'],
                'course': course_info['course'],
                'run': course_info['run'],
                'branch': branch,
                'structure': entry,
            }
            root = entry['root']
            course_list = self._load_items(envelope, [root], 0, lazy=True, **kwargs)
            if not isinstance(course_list[0], ErrorDescriptor):
                result.append(course_list[0])
        return result

    def make_course_key(self, org, course, run):
        """
        Return a valid :class:`~opaque_keys.edx.keys.CourseKey` for this modulestore
        that matches the supplied `org`, `course`, and `run`.

        This key may represent a course that doesn't exist in this modulestore.
        """
        return CourseLocator(org, course, run)

    def get_course(self, course_id, depth=0, **kwargs):
        '''
        Gets the course descriptor for the course identified by the locator
        '''
        if not isinstance(course_id, CourseLocator):
            # The supplied CourseKey is of the wrong type, so it can't possibly be stored in this modulestore.
            raise ItemNotFoundError(course_id)

        course_entry = self._lookup_course(course_id)
        root = course_entry['structure']['root']
        result = self._load_items(course_entry, [root], 0, lazy=True, **kwargs)
        return result[0]

    def has_course(self, course_id, ignore_case=False, **kwargs):
        '''
        Does this course exist in this modulestore. This method does not verify that the branch &/or
        version in the course_id exists. Use get_course_index_info to check that.

        Returns the course_id of the course if it was found, else None
        Note: we return the course_id instead of a boolean here since the found course may have
           a different id than the given course_id when ignore_case is True.
        '''
        if not isinstance(course_id, CourseLocator):
            # The supplied CourseKey is of the wrong type, so it can't possibly be stored in this modulestore.
            return False

        course_index = self.get_course_index(course_id, ignore_case)
        return CourseLocator(course_index['org'], course_index['course'], course_index['run'], course_id.branch) if course_index else None

    def has_item(self, usage_key):
        """
        Returns True if usage_key exists in its course. Returns false if
        the course or the block w/in the course do not exist for the given version.
        raises InsufficientSpecificationError if the usage_key does not id a block
        """
        if usage_key.block_id is None:
            raise InsufficientSpecificationError(usage_key)
        try:
            course_structure = self._lookup_course(usage_key.course_key)['structure']
        except ItemNotFoundError:
            # this error only occurs if the course does not exist
            return False

        return self._get_block_from_structure(course_structure, BlockKey.from_usage_key(usage_key)) is not None

    def get_item(self, usage_key, depth=0, **kwargs):
        """
        depth (int): An argument that some module stores may use to prefetch
            descendants of the queried modules for more efficient results later
            in the request. The depth is counted in the number of
            calls to get_children() to cache. None indicates to cache all
            descendants.
        raises InsufficientSpecificationError or ItemNotFoundError
        """
        if not isinstance(usage_key, BlockUsageLocator):
            # The supplied UsageKey is of the wrong type, so it can't possibly be stored in this modulestore.
            raise ItemNotFoundError(usage_key)

        course = self._lookup_course(usage_key.course_key)
        items = self._load_items(course, [BlockKey.from_usage_key(usage_key)], depth, lazy=True, **kwargs)
        if len(items) == 0:
            raise ItemNotFoundError(usage_key)
        elif len(items) > 1:
            log.debug("Found more than one item for '{}'".format(usage_key))
        return items[0]

    def get_items(self, course_locator, settings=None, content=None, qualifiers=None, **kwargs):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_locator

        NOTE: don't use this to look for courses as the course_locator is required. Use get_courses.

        Args:
            course_locator (CourseLocator): the course identifier
            settings (dict): fields to look for which have settings scope. Follows same syntax
                and rules as qualifiers below
            content (dict): fields to look for which have content scope. Follows same syntax and
                rules as qualifiers below.
            qualifiers (dict): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                For substring matching pass a regex object.
                For split,
                you can search by ``edited_by``, ``edited_on`` providing a function testing limits.
        """
        course = self._lookup_course(course_locator)
        items = []
        qualifiers = qualifiers.copy() if qualifiers else {}  # copy the qualifiers (destructively manipulated here)

        def _block_matches_all(block_json):
            """
            Check that the block matches all the criteria
            """
            # do the checks which don't require loading any additional data
            if (
                self._block_matches(block_json, qualifiers) and
                self._block_matches(block_json.get('fields', {}), settings)
            ):
                if content:
                    definition_block = self.db_connection.get_definition(block_json['definition'])
                    return self._block_matches(definition_block.get('fields', {}), content)
                else:
                    return True

        if settings is None:
            settings = {}
        if 'name' in qualifiers:
            # odd case where we don't search just confirm
            block_name = qualifiers.pop('name')
            block_ids = []
            for block_id, block in course['structure']['blocks'].iteritems():
                if block_name == block_id.id and _block_matches_all(block):
                    block_ids.append(block_id)

            return self._load_items(course, block_ids, lazy=True, **kwargs)

        if 'category' in qualifiers:
            qualifiers['block_type'] = qualifiers.pop('category')

        # don't expect caller to know that children are in fields
        if 'children' in qualifiers:
            settings['children'] = qualifiers.pop('children')
        for block_id, value in course['structure']['blocks'].iteritems():
            if _block_matches_all(value):
                items.append(block_id)

        if len(items) > 0:
            return self._load_items(course, items, 0, lazy=True, **kwargs)
        else:
            return []

    def get_parent_location(self, locator, **kwargs):
        '''
        Return the location (Locators w/ block_ids) for the parent of this location in this
        course. Could use get_items(location, {'children': block_id}) but this is slightly faster.
        NOTE: the locator must contain the block_id, and this code does not actually ensure block_id exists

        :param locator: BlockUsageLocator restricting search scope
        '''
        course = self._lookup_course(locator.course_key)
        parent_id = self._get_parent_from_structure(BlockKey.from_usage_key(locator), course['structure'])
        if parent_id is None:
            return None
        return BlockUsageLocator.make_relative(
            locator,
            block_type=parent_id.type,
            block_id=parent_id.id,
        )

    def get_orphans(self, course_key, **kwargs):
        """
        Return an array of all of the orphans in the course.
        """
        detached_categories = [name for name, __ in XBlock.load_tagged_classes("detached")]
        course = self._lookup_course(course_key)
        items = set(course['structure']['blocks'].keys())
        items.remove(course['structure']['root'])
        blocks = course['structure']['blocks']
        for block_id, block_data in blocks.iteritems():
            items.difference_update(BlockKey(*child) for child in block_data.get('fields', {}).get('children', []))
            if block_data['block_type'] in detached_categories:
                items.discard(block_id)
        return [
            course_key.make_usage_key(block_type=block_id.type, block_id=block_id.id)
            for block_id in items
        ]

    def get_course_index_info(self, course_key):
        """
        The index records the initial creation of the indexed course and tracks the current version
        heads. This function is primarily for test verification but may serve some
        more general purpose.
        :param course_key: must have a org, course, and run set
        :return {'org': string,
            versions: {'draft': the head draft version id,
                'published': the head published version id if any,
            },
            'edited_by': who created the course originally (named edited for consistency),
            'edited_on': when the course was originally created
        }
        """
        if not (course_key.course and course_key.run and course_key.org):
            return None
        index = self.get_course_index(course_key)
        return index

    # TODO figure out a way to make this info accessible from the course descriptor
    def get_course_history_info(self, course_key):
        """
        Because xblocks doesn't give a means to separate the course structure's meta information from
        the course xblock's, this method will get that info for the structure as a whole.
        :param course_key:
        :return {'original_version': the version guid of the original version of this course,
            'previous_version': the version guid of the previous version,
            'edited_by': who made the last change,
            'edited_on': when the change was made
        }
        """
        course = self._lookup_course(course_key)['structure']
        return {
            'original_version': course['original_version'],
            'previous_version': course['previous_version'],
            'edited_by': course['edited_by'],
            'edited_on': course['edited_on']
        }

    def get_definition_history_info(self, definition_locator):
        """
        Because xblocks doesn't give a means to separate the definition's meta information from
        the usage xblock's, this method will get that info for the definition
        :return {'original_version': the version guid of the original version of this course,
            'previous_version': the version guid of the previous version,
            'edited_by': who made the last change,
            'edited_on': when the change was made
        }
        """
        definition = self.db_connection.get_definition(definition_locator.definition_id)
        if definition is None:
            return None
        return definition['edit_info']

    def get_course_successors(self, course_locator, version_history_depth=1):
        '''
        Find the version_history_depth next versions of this course. Return as a VersionTree
        Mostly makes sense when course_locator uses a version_guid, but because it finds all relevant
        next versions, these do include those created for other courses.
        :param course_locator:
        '''
        if version_history_depth < 1:
            return None
        if course_locator.version_guid is None:
            course = self._lookup_course(course_locator)
            version_guid = course['structure']['_id']
            course_locator = course_locator.for_version(version_guid)
        else:
            version_guid = course_locator.version_guid

        # TODO if depth is significant, it may make sense to get all that have the same original_version
        # and reconstruct the subtree from version_guid
        next_entries = self.find_structures_derived_from([version_guid])
        # must only scan cursor's once
        next_versions = [struct for struct in next_entries]
        result = {version_guid: [CourseLocator(version_guid=struct['_id']) for struct in next_versions]}
        depth = 1
        while depth < version_history_depth and len(next_versions) > 0:
            depth += 1
            next_entries = self.find_structures_derived_from([struct['_id'] for struct in next_versions])
            next_versions = [struct for struct in next_entries]
            for course_structure in next_versions:
                result.setdefault(course_structure['previous_version'], []).append(
                    CourseLocator(version_guid=struct['_id']))
        return VersionTree(course_locator, result)

    def get_block_generations(self, block_locator):
        '''
        Find the history of this block. Return as a VersionTree of each place the block changed (except
        deletion).

        The block's history tracks its explicit changes but not the changes in its children starting
        from when the block was created.

        '''
        # course_agnostic means we don't care if the head and version don't align, trust the version
        course_struct = self._lookup_course(block_locator.course_key.course_agnostic())['structure']
        block_key = BlockKey.from_usage_key(block_locator)
        all_versions_with_block = self.find_ancestor_structures(
            original_version=course_struct['original_version'],
            block_key=block_key
        )
        # find (all) root versions and build map {previous: {successors}..}
        possible_roots = []
        result = {}
        for version in all_versions_with_block:
            block_payload = self._get_block_from_structure(version, block_key)
            if version['_id'] == block_payload['edit_info']['update_version']:
                if block_payload['edit_info'].get('previous_version') is None:
                    # this was when this block was created
                    possible_roots.append(block_payload['edit_info']['update_version'])
                else:  # map previous to {update..}
                    result.setdefault(block_payload['edit_info']['previous_version'], set()).add(
                        block_payload['edit_info']['update_version'])

        # more than one possible_root means usage was added and deleted > 1x.
        if len(possible_roots) > 1:
            # find the history segment including block_locator's version
            element_to_find = self._get_block_from_structure(course_struct, block_key)['edit_info']['update_version']
            if element_to_find in possible_roots:
                possible_roots = [element_to_find]
            for possibility in possible_roots:
                if self._find_local_root(element_to_find, possibility, result):
                    possible_roots = [possibility]
                    break
        elif len(possible_roots) == 0:
            return None
        # convert the results value sets to locators
        for k, versions in result.iteritems():
            result[k] = [
                block_locator.for_version(version)
                for version in versions
            ]
        return VersionTree(
            block_locator.for_version(possible_roots[0]),
            result
        )

    def get_definition_successors(self, definition_locator, version_history_depth=1):
        '''
        Find the version_history_depth next versions of this definition. Return as a VersionTree
        '''
        # TODO implement
        raise NotImplementedError()

    def create_definition_from_data(self, new_def_data, category, user_id):
        """
        Pull the definition fields out of descriptor and save to the db as a new definition
        w/o a predecessor and return the new id.

        :param user_id: request.user object
        """
        new_def_data = self._serialize_fields(category, new_def_data)
        new_id = ObjectId()
        document = {
            '_id': new_id,
            "block_type": category,
            "fields": new_def_data,
            "edit_info": {
                "edited_by": user_id,
                "edited_on": datetime.datetime.now(UTC),
                "previous_version": None,
                "original_version": new_id,
            },
            'schema_version': self.SCHEMA_VERSION,
        }
        self.db_connection.insert_definition(document)
        definition_locator = DefinitionLocator(category, new_id)
        return definition_locator

    def update_definition_from_data(self, definition_locator, new_def_data, user_id):
        """
        See if new_def_data differs from the persisted version. If so, update
        the persisted version and return the new id.

        :param user_id: request.user
        """
        def needs_saved():
            for key, value in new_def_data.iteritems():
                if key not in old_definition['fields'] or value != old_definition['fields'][key]:
                    return True
            for key, value in old_definition.get('fields', {}).iteritems():
                if key not in new_def_data:
                    return True

        # if this looks in cache rather than fresh fetches, then it will probably not detect
        # actual change b/c the descriptor and cache probably point to the same objects
        old_definition = self.db_connection.get_definition(definition_locator.definition_id)
        if old_definition is None:
            raise ItemNotFoundError(definition_locator)

        new_def_data = self._serialize_fields(old_definition['block_type'], new_def_data)
        if needs_saved():
            # new id to create new version
            old_definition['_id'] = ObjectId()
            old_definition['fields'] = new_def_data
            old_definition['edit_info']['edited_by'] = user_id
            old_definition['edit_info']['edited_on'] = datetime.datetime.now(UTC)
            # previous version id
            old_definition['edit_info']['previous_version'] = definition_locator.definition_id
            old_definition['schema_version'] = self.SCHEMA_VERSION
            self.db_connection.insert_definition(old_definition)
            return DefinitionLocator(old_definition['block_type'], old_definition['_id']), True
        else:
            return definition_locator, False

    def _generate_block_key(self, course_blocks, category):
        """
        Generate a somewhat readable block id unique w/in this course using the category
        :param course_blocks: the current list of blocks.
        :param category:
        """
        # NOTE: a potential bug is that a block is deleted and another created which gets the old
        # block's id. a possible fix is to cache the last serial in a dict in the structure
        # {category: last_serial...}
        # A potential confusion is if the name incorporates the parent's name, then if the child
        # moves, its id won't change and will be confusing
        serial = 1
        while True:
            potential_key = BlockKey(category, "{}{}".format(category, serial))
            if potential_key not in course_blocks:
                return potential_key
            serial += 1

    def create_item(
        self, user_id, course_key, block_type, block_id=None,
        definition_locator=None, fields=None,
        force=False, **kwargs
    ):
        """
        Add a descriptor to persistence as an element
        of the course. Return the resulting post saved version with populated locators.

        :param course_key: If it has a version_guid and a course org + course + run + branch, this
        method ensures that the version is the head of the given course branch before making the change.

        raises InsufficientSpecificationError if there is no course locator.
        raises VersionConflictError if the version_guid of the course_or_parent_locator is not the head
            of the its course unless force is true.
        :param force: fork the structure and don't update the course draftVersion if the above
        :param continue_revision: for multistep transactions, continue revising the given version rather than creating
        a new version. Setting force to True conflicts with setting this to True and will cause a VersionConflictError

        :param definition_locator: should either be None to indicate this is a brand new definition or
        a pointer to the existing definition to which this block should point or from which this was derived
        or a LocalId to indicate that it's new.
        If fields does not contain any Scope.content, then definition_locator must have a value meaning that this
        block points
        to the existing definition. If fields contains Scope.content and definition_locator is not None, then
        the Scope.content fields are assumed to be a new payload for definition_locator.

        :param block_id: if provided, must not already exist in the structure. Provides the block id for the
        new item in this structure. Otherwise, one is computed using the category appended w/ a few digits.

        This method creates a new version of the course structure unless the course has a bulk_write operation
        active.
        It creates and inserts the new block, makes the block point
        to the definition which may be new or a new version of an existing or an existing.

        Rules for course locator:

        * If the course locator specifies a org and course and run and either it doesn't
          specify version_guid or the one it specifies == the current head of the branch,
          it progresses the course to point
          to the new head and sets the active version to point to the new head
        * If the locator has a org and course and run but its version_guid != current head, it raises VersionConflictError.

        NOTE: using a version_guid will end up creating a new version of the course. Your new item won't be in
        the course id'd by version_guid but instead in one w/ a new version_guid. Ensure in this case that you get
        the new version_guid from the locator in the returned object!
        """
        with self.bulk_operations(course_key):
            # split handles all the fields in one dict not separated by scope
            fields = fields or {}
            fields.update(kwargs.pop('metadata', {}) or {})
            definition_data = kwargs.pop('definition_data', {})
            if definition_data:
                if not isinstance(definition_data, dict):
                    definition_data = {'data': definition_data}  # backward compatibility to mongo's hack
                fields.update(definition_data)

            # find course_index entry if applicable and structures entry
            index_entry = self._get_index_if_valid(course_key, force)
            structure = self._lookup_course(course_key)['structure']

            partitioned_fields = self.partition_fields_by_scope(block_type, fields)
            new_def_data = partitioned_fields.get(Scope.content, {})
            # persist the definition if persisted != passed
            if (definition_locator is None or isinstance(definition_locator.definition_id, LocalId)):
                definition_locator = self.create_definition_from_data(new_def_data, block_type, user_id)
            elif new_def_data is not None:
                definition_locator, _ = self.update_definition_from_data(definition_locator, new_def_data, user_id)

            # copy the structure and modify the new one
            new_structure = self.version_structure(course_key, structure, user_id)

            new_id = new_structure['_id']

            # generate usage id
            if block_id is not None:
                block_key = BlockKey(block_type, block_id)
                if block_key in new_structure['blocks']:
                    raise DuplicateItemError(block_id, self, 'structures')
            else:
                block_key = self._generate_block_key(new_structure['blocks'], block_type)

            block_fields = partitioned_fields.get(Scope.settings, {})
            if Scope.children in partitioned_fields:
                block_fields.update(partitioned_fields[Scope.children])
            self._update_block_in_structure(new_structure, block_key, self._new_block(
                user_id,
                block_type,
                block_fields,
                definition_locator.definition_id,
                new_id,
            ))

            self.update_structure(course_key, new_structure)

            # update the index entry if appropriate
            if index_entry is not None:
                # see if any search targets changed
                if fields is not None:
                    self._update_search_targets(index_entry, fields)
                self._update_head(course_key, index_entry, course_key.branch, new_id)
                item_loc = BlockUsageLocator(
                    course_key.version_agnostic(),
                    block_type=block_type,
                    block_id=block_key.id,
                )
            else:
                item_loc = BlockUsageLocator(
                    CourseLocator(version_guid=new_id),
                    block_type=block_type,
                    block_id=block_key.id,
                )

            # reconstruct the new_item from the cache
            return self.get_item(item_loc)

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, fields=None, **kwargs):
        """
        Creates and saves a new xblock that as a child of the specified block

        Returns the newly created item.

        Args:
            user_id: ID of the user creating and saving the xmodule
            parent_usage_key: a :class:`~opaque_key.edx.UsageKey` identifying the
                block that this item should be parented under
            block_type: The typo of block to create
            block_id: a unique identifier for the new item. If not supplied,
                a new identifier will be generated
            fields (dict): A dictionary specifying initial values for some or all fields
                in the newly created block
        """
        with self.bulk_operations(parent_usage_key.course_key):
            xblock = self.create_item(
                user_id, parent_usage_key.course_key, block_type, block_id=block_id, fields=fields,
                **kwargs)

            # don't version the structure as create_item handled that already.
            new_structure = self._lookup_course(xblock.location.course_key)['structure']

            # add new block as child and update parent's version
            block_id = BlockKey.from_usage_key(parent_usage_key)
            if block_id not in new_structure['blocks']:
                raise ItemNotFoundError(parent_usage_key)

            parent = new_structure['blocks'][block_id]
            parent['fields'].setdefault('children', []).append(BlockKey.from_usage_key(xblock.location))
            if parent['edit_info']['update_version'] != new_structure['_id']:
                # if the parent hadn't been previously changed in this bulk transaction, indicate that it's
                # part of the bulk transaction
                self.version_block(parent, user_id, new_structure['_id'])

            # db update
            self.update_structure(parent_usage_key.course_key, new_structure)

        # don't need to update the index b/c create_item did it for this version
        return xblock

    def clone_course(self, source_course_id, dest_course_id, user_id, fields=None, **kwargs):
        """
        See :meth: `.ModuleStoreWrite.clone_course` for documentation.

        In split, other than copying the assets, this is cheap as it merely creates a new version of the
        existing course.
        """
        source_index = self.get_course_index_info(source_course_id)
        if source_index is None:
            raise ItemNotFoundError("Cannot find a course at {0}. Aborting".format(source_course_id))
        new_course = self.create_course(
            dest_course_id.org, dest_course_id.course, dest_course_id.run,
            user_id,
            fields=fields,
            versions_dict=source_index['versions'],
            search_targets=source_index['search_targets'],
            skip_auto_publish=True,
            **kwargs
        )
        # don't copy assets until we create the course in case something's awry
        super(SplitMongoModuleStore, self).clone_course(source_course_id, dest_course_id, user_id, fields, **kwargs)
        return new_course

    DEFAULT_ROOT_BLOCK_ID = 'course'
    def create_course(
        self, org, course, run, user_id, master_branch=None, fields=None,
        versions_dict=None, search_targets=None, root_category='course',
        root_block_id=None, **kwargs
    ):
        """
        Create a new entry in the active courses index which points to an existing or new structure. Returns
        the course root of the resulting entry (the location has the course id)

        Arguments:

            org (str): the organization that owns the course
            course (str): the course number of the course
            run (str): the particular run of the course (e.g. 2013_T1)
            user_id: id of the user creating the course
            fields (dict): Fields to set on the course at initialization
            kwargs: Any optional arguments understood by a subset of modulestores to customize instantiation

        course + run: If there are duplicates, this method will raise DuplicateCourseError

        fields: if scope.settings fields provided, will set the fields of the root course object in the
        new course. If both
        settings fields and a starting version are provided (via versions_dict), it will generate a successor version
        to the given version,
        and update the settings fields with any provided values (via update not setting).

        fields (content): if scope.content fields provided, will update the fields of the new course
        xblock definition to this. Like settings fields,
        if provided, this will cause a new version of any given version as well as a new version of the
        definition (which will point to the existing one if given a version). If not provided and given
        a version_dict, it will reuse the same definition as that version's course
        (obvious since it's reusing the
        course). If not provided and no version_dict is given, it will be empty and get the field defaults
        when
        loaded.

        master_branch: the tag (key) for the version name in the dict which is the DRAFT version. Not the actual
        version guid, but what to call it.

        search_targets: a dict of search key and value. For example, wiki_slug. Add any fields whose edits
        should change the search targets to SplitMongoModuleStore.SEARCH_TARGET dict

        versions_dict: the starting version ids where the keys are the tags such as DRAFT and PUBLISHED
        and the values are structure guids. If provided, the new course will reuse this version (unless you also
        provide any fields overrides, see above). if not provided, will create a mostly empty course
        structure with just a category course root xblock.
        """
        # either need to assert this or have a default
        assert master_branch is not None
        # check course and run's uniqueness
        locator = CourseLocator(org=org, course=course, run=run, branch=master_branch)
        index = self.get_course_index(locator)
        if index is not None:
            raise DuplicateCourseError(locator, index)

        partitioned_fields = self.partition_fields_by_scope(root_category, fields)
        block_fields = partitioned_fields[Scope.settings]
        if Scope.children in partitioned_fields:
            block_fields.update(partitioned_fields[Scope.children])
        definition_fields = self._serialize_fields(root_category, partitioned_fields.get(Scope.content, {}))

        # build from inside out: definition, structure, index entry
        # if building a wholly new structure
        if versions_dict is None or master_branch not in versions_dict:
            # create new definition and structure
            definition_id = ObjectId()
            definition_entry = {
                '_id': definition_id,
                'block_type': root_category,
                'fields': definition_fields,
                'edit_info': {
                    'edited_by': user_id,
                    'edited_on': datetime.datetime.now(UTC),
                    'previous_version': None,
                    'original_version': definition_id,
                },
                'schema_version': self.SCHEMA_VERSION,
            }
            self.db_connection.insert_definition(definition_entry)

            draft_structure = self._new_structure(
                user_id,
                BlockKey(
                    root_category,
                    root_block_id or SplitMongoModuleStore.DEFAULT_ROOT_BLOCK_ID,
                ),
                block_fields,
                definition_id
            )
            new_id = draft_structure['_id']

            if versions_dict is None:
                versions_dict = {master_branch: new_id}
            else:
                versions_dict[master_branch] = new_id

        elif block_fields or definition_fields:  # pointing to existing course w/ some overrides
            # just get the draft_version structure
            draft_version = CourseLocator(version_guid=versions_dict[master_branch])
            draft_structure = self._lookup_course(draft_version)['structure']
            draft_structure = self.version_structure(locator, draft_structure, user_id)
            new_id = draft_structure['_id']
            root_block = draft_structure['blocks'][draft_structure['root']]
            if block_fields is not None:
                root_block['fields'].update(self._serialize_fields(root_category, block_fields))
            if definition_fields is not None:
                definition = self.db_connection.get_definition(root_block['definition'])
                definition['fields'].update(definition_fields)
                definition['edit_info']['previous_version'] = definition['_id']
                definition['edit_info']['edited_by'] = user_id
                definition['edit_info']['edited_on'] = datetime.datetime.now(UTC)
                definition['_id'] = ObjectId()
                definition['schema_version'] = self.SCHEMA_VERSION
                self.db_connection.insert_definition(definition)
                root_block['definition'] = definition['_id']
                root_block['edit_info']['edited_on'] = datetime.datetime.now(UTC)
                root_block['edit_info']['edited_by'] = user_id
                root_block['edit_info']['previous_version'] = root_block['edit_info'].get('update_version')
                root_block['edit_info']['update_version'] = new_id

            versions_dict[master_branch] = new_id
        else:  # Pointing to an existing course structure
            new_id = versions_dict[master_branch]
            draft_version = CourseLocator(version_guid=new_id)
            draft_structure = self._lookup_course(draft_version)['structure']

        locator = locator.replace(version_guid=new_id)
        with self.bulk_operations(locator):
            self.update_structure(locator, draft_structure)
            index_entry = {
                '_id': ObjectId(),
                'org': org,
                'course': course,
                'run': run,
                'edited_by': user_id,
                'edited_on': datetime.datetime.now(UTC),
                'versions': versions_dict,
                'schema_version': self.SCHEMA_VERSION,
                'search_targets': search_targets or {},
            }
            if fields is not None:
                self._update_search_targets(index_entry, fields)
            self.insert_course_index(locator, index_entry)

            # expensive hack to persist default field values set in __init__ method (e.g., wiki_slug)
            course = self.get_course(locator, **kwargs)
            return self.update_item(course, user_id, **kwargs)

    def update_item(self, descriptor, user_id, allow_not_found=False, force=False, **kwargs):
        """
        Save the descriptor's fields. it doesn't descend the course dag to save the children.
        Return the new descriptor (updated location).

        raises ItemNotFoundError if the location does not exist.

        Creates a new course version. If the descriptor's location has a org and course and run, it moves the course head
        pointer. If the version_guid of the descriptor points to a non-head version and there's been an intervening
        change to this item, it raises a VersionConflictError unless force is True. In the force case, it forks
        the course but leaves the head pointer where it is (this change will not be in the course head).

        The implementation tries to detect which, if any changes, actually need to be saved and thus won't version
        the definition, structure, nor course if they didn't change.
        """
        partitioned_fields = self.partition_xblock_fields_by_scope(descriptor)
        return self._update_item_from_fields(
            user_id, descriptor.location.course_key, BlockKey.from_usage_key(descriptor.location),
            partitioned_fields, descriptor.definition_locator, allow_not_found, force, **kwargs
        ) or descriptor

    def _update_item_from_fields(
        self, user_id, course_key, block_key, partitioned_fields,
        definition_locator, allow_not_found, force, **kwargs
    ):
        """
        Broke out guts of update_item for short-circuited internal use only
        """
        with self.bulk_operations(course_key):
            if allow_not_found and isinstance(block_key.id, (LocalId, NoneType)):
                fields = {}
                for subfields in partitioned_fields.itervalues():
                    fields.update(subfields)
                return self.create_item(
                    user_id, course_key, block_key.type, fields=fields, force=force
                )

            original_structure = self._lookup_course(course_key)['structure']
            index_entry = self._get_index_if_valid(course_key, force)

            original_entry = self._get_block_from_structure(original_structure, block_key)
            if original_entry is None:
                if allow_not_found:
                    fields = {}
                    for subfields in partitioned_fields.itervalues():
                        fields.update(subfields)
                    return self.create_item(
                        user_id, course_key, block_key.type, block_id=block_key.id, fields=fields, force=force,
                    )
                else:
                    raise ItemNotFoundError(course_key.make_usage_key(block_key.type, block_key.id))

            is_updated = False
            definition_fields = partitioned_fields[Scope.content]
            if definition_locator is None:
                definition_locator = DefinitionLocator(original_entry['block_type'], original_entry['definition'])
            if definition_fields:
                definition_locator, is_updated = self.update_definition_from_data(
                    definition_locator, definition_fields, user_id
                )

            # check metadata
            settings = partitioned_fields[Scope.settings]
            settings = self._serialize_fields(block_key.type, settings)
            if not is_updated:
                is_updated = self._compare_settings(settings, original_entry['fields'])

            # check children
            if partitioned_fields.get(Scope.children, {}):  # purposely not 'is not None'
                serialized_children = [BlockKey.from_usage_key(child) for child in partitioned_fields[Scope.children]['children']]
                is_updated = is_updated or original_entry['fields'].get('children', []) != serialized_children
                if is_updated:
                    settings['children'] = serialized_children

            # if updated, rev the structure
            if is_updated:
                new_structure = self.version_structure(course_key, original_structure, user_id)
                block_data = self._get_block_from_structure(new_structure, block_key)

                block_data["definition"] = definition_locator.definition_id
                block_data["fields"] = settings

                new_id = new_structure['_id']
                self.version_block(block_data, user_id, new_id)
                self.update_structure(course_key, new_structure)
                # update the index entry if appropriate
                if index_entry is not None:
                    self._update_search_targets(index_entry, definition_fields)
                    self._update_search_targets(index_entry, settings)
                    course_key = CourseLocator(
                        org=index_entry['org'],
                        course=index_entry['course'],
                        run=index_entry['run'],
                        branch=course_key.branch,
                        version_guid=new_id
                    )
                    self._update_head(course_key, index_entry, course_key.branch, new_id)
                else:
                    course_key = CourseLocator(version_guid=new_id)

                # fetch and return the new item--fetching is unnecessary but a good qc step
                new_locator = course_key.make_usage_key(block_key.type, block_key.id)
                return self.get_item(new_locator, **kwargs)
            else:
                return None

    # pylint: disable=unused-argument
    def create_xblock(
            self, runtime, course_key, block_type, block_id=None, fields=None,
            definition_id=None, parent_xblock=None, **kwargs
    ):
        """
        This method instantiates the correct subclass of XModuleDescriptor based
        on the contents of json_data. It does not persist it and can create one which
        has no usage id.

        parent_xblock is used to compute inherited metadata as well as to append the new xblock.

        json_data:
        - 'block_type': the xmodule block_type
        - 'fields': a dict of locally set fields (not inherited) in json format not pythonic typed format!
        - 'definition': the object id of the existing definition
        """
        assert runtime is not None

        xblock_class = runtime.load_block_type(block_type)
        json_data = {
            'block_type': block_type,
            'fields': {},
        }
        if definition_id is not None:
            json_data['definition'] = definition_id
        if parent_xblock is None:
            # If no parent, then nothing to inherit.
            inherited_settings = {}
        else:
            inherited_settings = parent_xblock.xblock_kvs.inherited_settings.copy()
            if fields is not None:
                for field_name in inheritance.InheritanceMixin.fields:
                    if field_name in fields:
                        inherited_settings[field_name] = fields[field_name]

        new_block = runtime.xblock_from_json(
            xblock_class,
            course_key,
            BlockKey(block_type, block_id) if block_id else None,
            json_data,
            inherited_settings,
            **kwargs
        )
        for field_name, value in (fields or {}).iteritems():
            setattr(new_block, field_name, value)

        if parent_xblock is not None:
            parent_xblock.children.append(new_block.scope_ids.usage_id)
            # decache pending children field settings
            parent_xblock.save()
        return new_block

    def persist_xblock_dag(self, xblock, user_id, force=False):
        """
        create or update the xblock and all of its children. The xblock's location must specify a course.
        If it doesn't specify a usage_id, then it's presumed to be new and need creation. This function
        descends the children performing the same operation for any that are xblocks. Any children which
        are block_ids just update the children pointer.

        All updates go into the same course version (bulk updater).

        Updates the objects which came in w/ updated location and definition_location info.

        returns the post-persisted version of the incoming xblock. Note that its children will be ids not
        objects.

        :param xblock: the head of the dag
        :param user_id: who's doing the change
        """
        # find course_index entry if applicable and structures entry
        course_key = xblock.location.course_key
        with self.bulk_operations(course_key):
            index_entry = self._get_index_if_valid(course_key, force)
            structure = self._lookup_course(course_key)['structure']
            new_structure = self.version_structure(course_key, structure, user_id)
            new_id = new_structure['_id']
            is_updated = self._persist_subdag(xblock, user_id, new_structure['blocks'], new_id)

            if is_updated:
                self.update_structure(course_key, new_structure)

                # update the index entry if appropriate
                if index_entry is not None:
                    self._update_head(course_key, index_entry, xblock.location.branch, new_id)

                # fetch and return the new item--fetching is unnecessary but a good qc step
                return self.get_item(xblock.location.for_version(new_id))
            else:
                return xblock

    def _persist_subdag(self, xblock, user_id, structure_blocks, new_id):
        # persist the definition if persisted != passed
        partitioned_fields = self.partition_xblock_fields_by_scope(xblock)
        new_def_data = self._serialize_fields(xblock.category, partitioned_fields[Scope.content])
        is_updated = False
        if xblock.definition_locator is None or isinstance(xblock.definition_locator.definition_id, LocalId):
            xblock.definition_locator = self.create_definition_from_data(
                new_def_data, xblock.category, user_id)
            is_updated = True
        elif new_def_data:
            xblock.definition_locator, is_updated = self.update_definition_from_data(
                xblock.definition_locator, new_def_data, user_id)

        if isinstance(xblock.scope_ids.usage_id.block_id, LocalId):
            # generate an id
            is_new = True
            is_updated = True
            block_id = getattr(xblock.scope_ids.usage_id.block_id, 'block_id', None)
            if block_id is None:
                block_key = self._generate_block_key(structure_blocks, xblock.scope_ids.block_type)
            else:
                block_key = BlockKey(xblock.scope_ids.block_type, block_id)
            new_usage_id = xblock.scope_ids.usage_id.replace(block_id=block_key.id)
            xblock.scope_ids = xblock.scope_ids._replace(usage_id=new_usage_id)  # pylint: disable=protected-access
        else:
            is_new = False
            block_key = BlockKey(xblock.scope_ids.block_type, xblock.scope_ids.usage_id.block_id)

        children = []
        if xblock.has_children:
            for child in xblock.children:
                if isinstance(child.block_id, LocalId):
                    child_block = xblock.system.get_block(child)
                    is_updated = self._persist_subdag(child_block, user_id, structure_blocks, new_id) or is_updated
                    children.append(BlockKey.from_usage_key(child_block.location))
                else:
                    children.append(BlockKey.from_usage_key(child))
            is_updated = is_updated or structure_blocks[block_key]['fields']['children'] != children

        block_fields = partitioned_fields[Scope.settings]
        block_fields = self._serialize_fields(xblock.category, block_fields)
        if not is_new and not is_updated:
            is_updated = self._compare_settings(block_fields, structure_blocks[block_key]['fields'])
        if children:
            block_fields['children'] = children

        if is_updated:
            if is_new:
                block_info = self._new_block(
                    user_id,
                    xblock.category,
                    block_fields,
                    xblock.definition_locator.definition_id,
                    new_id,
                    raw=True
                )
            else:
                block_info = structure_blocks[block_key]
                block_info['fields'] = block_fields
                block_info['definition'] = xblock.definition_locator.definition_id
                self.version_block(block_info, user_id, new_id)

            structure_blocks[block_key] = block_info

        return is_updated

    def _compare_settings(self, settings, original_fields):
        """
        Return True if the settings are not == to the original fields
        :param settings:
        :param original_fields:
        """
        original_keys = original_fields.keys()
        if 'children' in original_keys:
            original_keys.remove('children')
        if len(settings) != len(original_keys):
            return True
        else:
            new_keys = settings.keys()
            for key in original_keys:
                if key not in new_keys or original_fields[key] != settings[key]:
                    return True

    def copy(self, user_id, source_course, destination_course, subtree_list=None, blacklist=None):
        """
        Copies each xblock in subtree_list and those blocks descendants excluding blacklist
        from source_course to destination_course.

        To delete a block in the destination_course, copy its parent and blacklist the other
        sibs to keep them from being copies. You can also just call delete_item on the destination.

        Ensures that each subtree occurs in the same place in destination as it does in source. If any
        of the source's subtree parents are missing from destination, it raises ItemNotFound([parent_ids]).
        To determine the same relative order vis-a-vis published siblings,
        publishing may involve changing the order of previously published siblings. For example,
        if publishing `[c, d]` and source parent has children `[a, b, c, d, e]` and destination parent
        currently has children `[e, b]`, there's no obviously correct resulting order; thus, publish will
        reorder destination to `[b, c, d, e]` to make it conform with the source.

        :param source_course: a CourseLocator (can be a version or course w/ branch)

        :param destination_course: a CourseLocator which must be an existing course but branch doesn't have
        to exist yet. (The course must exist b/c Locator doesn't have everything necessary to create it).
        Note, if the branch doesn't exist, then the source_course structure's root must be in subtree_list;
        otherwise, the publish will violate the parents must exist rule.

        :param subtree_list: a list of usage keys whose subtrees to publish.

        :param blacklist: a list of usage keys to not change in the destination: i.e., don't add
        if not there, don't update if there.

        Raises:
            ItemNotFoundError: if it cannot find the course. if the request is to publish a
                subtree but the ancestors up to and including the course root are not published.
        """
        # get the destination's index, and source and destination structures.
        with self.bulk_operations(source_course):
            with self.bulk_operations(destination_course):
                source_structure = self._lookup_course(source_course)['structure']
                index_entry = self.get_course_index(destination_course)
                if index_entry is None:
                    # brand new course
                    raise ItemNotFoundError(destination_course)
                if destination_course.branch not in index_entry['versions']:
                    # must be copying the dag root if there's no current dag
                    root_block_key = source_structure['root']
                    if not any(root_block_key == BlockKey.from_usage_key(subtree) for subtree in subtree_list):
                        raise ItemNotFoundError(u'Must publish course root {}'.format(root_block_key))
                    root_source = source_structure['blocks'][root_block_key]
                    # create branch
                    destination_structure = self._new_structure(
                        user_id, root_block_key,
                        # leave off the fields b/c the children must be filtered
                        definition_id=root_source['definition'],
                    )
                else:
                    destination_structure = self._lookup_course(destination_course)['structure']
                    destination_structure = self.version_structure(destination_course, destination_structure, user_id)

                if blacklist != EXCLUDE_ALL:
                    blacklist = [BlockKey.from_usage_key(shunned) for shunned in blacklist or []]
                # iterate over subtree list filtering out blacklist.
                orphans = set()
                destination_blocks = destination_structure['blocks']
                for subtree_root in subtree_list:
                    if BlockKey.from_usage_key(subtree_root) != source_structure['root']:
                        # find the parents and put root in the right sequence
                        parent = self._get_parent_from_structure(BlockKey.from_usage_key(subtree_root), source_structure)
                        if parent is not None:  # may be a detached category xblock
                            if not parent in destination_blocks:
                                raise ItemNotFoundError(parent)
                            orphans.update(
                                self._sync_children(
                                    source_structure['blocks'][parent],
                                    destination_blocks[parent],
                                    BlockKey.from_usage_key(subtree_root)
                                )
                            )
                    # update/create the subtree and its children in destination (skipping blacklist)
                    orphans.update(
                        self._copy_subdag(
                            user_id, destination_structure['_id'],
                            BlockKey.from_usage_key(subtree_root),
                            source_structure['blocks'],
                            destination_blocks,
                            blacklist
                        )
                    )
                # remove any remaining orphans
                for orphan in orphans:
                    # orphans will include moved as well as deleted xblocks. Only delete the deleted ones.
                    self._delete_if_true_orphan(orphan, destination_structure)

                # update the db
                self.update_structure(destination_course, destination_structure)
                self._update_head(destination_course, index_entry, destination_course.branch, destination_structure['_id'])

    def delete_item(self, usage_locator, user_id, force=False):
        """
        Delete the block or tree rooted at block (if delete_children) and any references w/in the course to the block
        from a new version of the course structure.

        returns CourseLocator for new version

        raises ItemNotFoundError if the location does not exist.
        raises ValueError if usage_locator points to the structure root

        Creates a new course version. If the descriptor's location has a org, a course, and a run, it moves the course head
        pointer. If the version_guid of the descriptor points to a non-head version and there's been an intervening
        change to this item, it raises a VersionConflictError unless force is True. In the force case, it forks
        the course but leaves the head pointer where it is (this change will not be in the course head).
        """
        if not isinstance(usage_locator, BlockUsageLocator):
            # The supplied UsageKey is of the wrong type, so it can't possibly be stored in this modulestore.
            raise ItemNotFoundError(usage_locator)

        with self.bulk_operations(usage_locator.course_key):
            original_structure = self._lookup_course(usage_locator.course_key)['structure']
            block_key = BlockKey.from_usage_key(usage_locator)
            if original_structure['root'] == block_key:
                raise ValueError("Cannot delete the root of a course")
            if block_key not in original_structure['blocks']:
                raise ValueError("Cannot delete a block that does not exist")
            index_entry = self._get_index_if_valid(usage_locator.course_key, force)
            new_structure = self.version_structure(usage_locator.course_key, original_structure, user_id)
            new_blocks = new_structure['blocks']
            new_id = new_structure['_id']
            parent_block_key = self._get_parent_from_structure(block_key, original_structure)
            if parent_block_key:
                parent_block = new_blocks[parent_block_key]
                parent_block['fields']['children'].remove(block_key)
                parent_block['edit_info']['edited_on'] = datetime.datetime.now(UTC)
                parent_block['edit_info']['edited_by'] = user_id
                parent_block['edit_info']['previous_version'] = parent_block['edit_info']['update_version']
                parent_block['edit_info']['update_version'] = new_id

            self._remove_subtree(BlockKey.from_usage_key(usage_locator), new_blocks)

            # update index if appropriate and structures
            self.update_structure(usage_locator.course_key, new_structure)

            if index_entry is not None:
                # update the index entry if appropriate
                self._update_head(usage_locator.course_key, index_entry, usage_locator.branch, new_id)
                result = usage_locator.course_key.for_version(new_id)
            else:
                result = CourseLocator(version_guid=new_id)

            return result

    @contract(block_key=BlockKey, blocks='dict(BlockKey: dict)')
    def _remove_subtree(self, block_key, blocks):
        """
        Remove the subtree rooted at block_key
        """
        for child in blocks[block_key]['fields'].get('children', []):
            self._remove_subtree(BlockKey(*child), blocks)
        del blocks[block_key]

    def delete_course(self, course_key, user_id):
        """
        Remove the given course from the course index.

        Only removes the course from the index. The data remains. You can use create_course
        with a versions hash to restore the course; however, the edited_on and
        edited_by won't reflect the originals, of course.
        """
        index = self.get_course_index(course_key)
        if index is None:
            raise ItemNotFoundError(course_key)
        # this is the only real delete in the system. should it do something else?
        log.info(u"deleting course from split-mongo: %s", course_key)
        self.db_connection.delete_course_index(index)

        # We do NOT call the super class here since we need to keep the assets
        # in case the course is later restored.
        # super(SplitMongoModuleStore, self).delete_course(course_key, user_id)

    @contract(block_map="dict(BlockKey: dict)", block_key=BlockKey)
    def inherit_settings(
        self, block_map, block_key, inherited_settings_map, inheriting_settings=None, inherited_from=None
    ):
        """
        Updates block_json with any inheritable setting set by an ancestor and recurses to children.
        """
        if block_key not in block_map:
            return
        block_json = block_map[block_key]

        if inheriting_settings is None:
            inheriting_settings = {}

        if inherited_from is None:
            inherited_from = []

        # the currently passed down values take precedence over any previously cached ones
        # NOTE: this should show the values which all fields would have if inherited: i.e.,
        # not set to the locally defined value but to value set by nearest ancestor who sets it
        inherited_settings_map.setdefault(block_key, {}).update(inheriting_settings)

        # update the inheriting w/ what should pass to children
        inheriting_settings = inherited_settings_map[block_key].copy()
        block_fields = block_json['fields']
        for field_name in inheritance.InheritanceMixin.fields:
            if field_name in block_fields:
                inheriting_settings[field_name] = block_fields[field_name]

        for child in block_fields.get('children', []):
            try:
                if child in inherited_from:
                    raise Exception(u'Infinite loop detected when inheriting to {}, having already inherited from {}'.format(child, inherited_from))
                self.inherit_settings(
                    block_map,
                    BlockKey(*child),
                    inherited_settings_map,
                    inheriting_settings,
                    inherited_from + [child]
                )
            except KeyError:
                # here's where we need logic for looking up in other structures when we allow cross pointers
                # but it's also getting this during course creation if creating top down w/ children set or
                # migration where the old mongo published had pointers to privates
                pass

    def descendants(self, block_map, block_id, depth, descendent_map):
        """
        adds block and its descendants out to depth to descendent_map
        Depth specifies the number of levels of descendants to return
        (0 => this usage only, 1 => this usage and its children, etc...)
        A depth of None returns all descendants
        """
        if block_id not in block_map:
            return descendent_map

        if block_id not in descendent_map:
            descendent_map[block_id] = block_map[block_id]

        if depth is None or depth > 0:
            depth = depth - 1 if depth is not None else None
            for child in descendent_map[block_id]['fields'].get('children', []):
                descendent_map = self.descendants(block_map, child, depth, descendent_map)

        return descendent_map

    def get_modulestore_type(self, course_key=None):
        """
        Returns an enumeration-like type reflecting the type of this modulestore, per ModuleStoreEnum.Type.

        Args:
            course_key: just for signature compatibility
        """
        return ModuleStoreEnum.Type.split

    def internal_clean_children(self, course_locator):
        """
        Only intended for rather low level methods to use. Goes through the children attrs of
        each block removing any whose block_id is not a member of the course. Does not generate
        a new version of the course but overwrites the existing one.

        :param course_locator: the course to clean
        """
        original_structure = self._lookup_course(course_locator)['structure']
        for block in original_structure['blocks'].itervalues():
            if 'fields' in block and 'children' in block['fields']:
                block['fields']["children"] = [
                    block_id for block_id in block['fields']["children"]
                    if block_id in original_structure['blocks']
                ]
        self.update_structure(course_locator, original_structure)

    def convert_references_to_keys(self, course_key, xblock_class, jsonfields, blocks):
        """
        Convert the given serialized fields to the deserialized values by finding all references
        and converting them.
        :param jsonfields: the serialized copy of the xblock's fields
        """
        @contract(block_key="BlockUsageLocator | seq[2]")
        def robust_usage_key(block_key):
            """
            create a course_key relative usage key for the block_key. If the block_key is in blocks,
            use its correct category; otherwise, use 'unknown'.
            The purpose for this is that some operations add pointers as they build up the
            structure without worrying about order of creation. Because the category of the
            usage_key is for the most part inert, it's better to hack a value than to work
            out a dependency graph algorithm for those functions which may prereference blocks.
            """
            # if this was taken from cache, then its fields are already converted
            if isinstance(block_key, BlockUsageLocator):
                return block_key.map_into_course(course_key)
            elif not isinstance(block_key, BlockKey):
                block_key = BlockKey(*block_key)

            try:
                return course_key.make_usage_key(
                    block_key.type, block_key.id
                )
            except KeyError:
                return course_key.make_usage_key('unknown', block_key.id)

        xblock_class = self.mixologist.mix(xblock_class)
        # Make a shallow copy, so that we aren't manipulating a cached field dictionary
        output_fields = dict(jsonfields)
        for field_name, value in output_fields.iteritems():
            if value:
                field = xblock_class.fields.get(field_name)
                if field is None:
                    continue
                elif isinstance(field, Reference):
                    output_fields[field_name] = robust_usage_key(value)
                elif isinstance(field, ReferenceList):
                    output_fields[field_name] = [robust_usage_key(ele) for ele in value]
                elif isinstance(field, ReferenceValueDict):
                    for key, subvalue in value.iteritems():
                        value[key] = robust_usage_key(subvalue)
        return output_fields

    def _get_index_if_valid(self, course_key, force=False):
        """
        If the course_key identifies a course and points to its draft (or plausibly its draft),
        then return the index entry.

        raises VersionConflictError if not the right version

        :param course_key: a CourseLocator
        :param force: if false, raises VersionConflictError if the current head of the course != the one identified
        by course_key
        """
        if course_key.org is None or course_key.course is None or course_key.run is None or course_key.branch is None:
            return None
        else:
            index_entry = self.get_course_index(course_key)
            is_head = (
                course_key.version_guid is None or
                index_entry['versions'][course_key.branch] == course_key.version_guid
            )
            if (is_head or force):
                return index_entry
            else:
                raise VersionConflictError(
                    course_key,
                    index_entry['versions'][course_key.branch]
                )

    def _find_local_root(self, element_to_find, possibility, tree):
        if possibility not in tree:
            return False
        if element_to_find in tree[possibility]:
            return True
        for subtree in tree[possibility]:
            if self._find_local_root(element_to_find, subtree, tree):
                return True
        return False

    def _update_search_targets(self, index_entry, fields):
        """
        Update the index entry if any of the given fields are in SEARCH_TARGET_DICT. (doesn't save
        the changes, just changes them in the entry dict)
        :param index_entry:
        :param fields: a dictionary of fields and values usually only those explicitly set and already
            ready for persisting (e.g., references converted to block_ids)
        """
        for field_name, field_value in fields.iteritems():
            if field_name in self.SEARCH_TARGET_DICT:
                index_entry.setdefault('search_targets', {})[field_name] = field_value

    def _update_head(self, course_key, index_entry, branch, new_id):
        """
        Update the active index for the given course's branch to point to new_id

        :param index_entry:
        :param course_locator:
        :param new_id:
        """
        if not isinstance(new_id, ObjectId):
            raise TypeError('new_id must be an ObjectId, but is {!r}'.format(new_id))
        index_entry['versions'][branch] = new_id
        self.update_course_index(course_key, index_entry)

    def partition_xblock_fields_by_scope(self, xblock):
        """
        Return a dictionary of scopes mapped to this xblock's explicitly set fields w/o any conversions
        """
        # explicitly_set_fields_by_scope converts to json; so, avoiding it
        # the existing partition_fields_by_scope works on a dict not an xblock
        result = defaultdict(dict)
        for field in xblock.fields.itervalues():
            if field.is_set_on(xblock):
                result[field.scope][field.name] = field.read_from(xblock)
        return result

    def _serialize_fields(self, category, fields):
        """
        Convert any references to their serialized form. Handle some references already being unicoded
        because the client passed them that way and nothing above this layer did the necessary deserialization.

        Remove any fields which split or its kvs computes or adds but does not want persisted.

        :param fields: a dict of fields
        """
        assert isinstance(fields, dict)
        xblock_class = XBlock.load_class(category, self.default_class)
        xblock_class = self.mixologist.mix(xblock_class)

        def reference_block_id(reference):
            """
            Handle client possibly setting field to strings rather than keys to get the block_id
            """
            # perhaps replace by fixing the views or Field Reference*.from_json to return a Key
            if isinstance(reference, basestring):
                reference = BlockUsageLocator.from_string(reference)
            return BlockKey.from_usage_key(reference)

        for field_name, value in fields.iteritems():
            if value is not None:
                if isinstance(xblock_class.fields[field_name], Reference):
                    fields[field_name] = reference_block_id(value)
                elif isinstance(xblock_class.fields[field_name], ReferenceList):
                    fields[field_name] = [
                        reference_block_id(ele) for ele in value
                    ]
                elif isinstance(xblock_class.fields[field_name], ReferenceValueDict):
                    for key, subvalue in value.iteritems():
                        value[key] = reference_block_id(subvalue)
                # should this recurse down dicts and lists just in case they contain datetime?
                elif not isinstance(value, datetime.datetime):  # don't convert datetimes!
                    fields[field_name] = xblock_class.fields[field_name].to_json(value)
        return fields

    def _new_structure(self, user_id, root_block_key, block_fields=None, definition_id=None):
        """
        Internal function: create a structure element with no previous version. Must provide the root id
        but not necessarily the info needed to create it (for the use case of publishing). If providing
        root_category, must also provide block_fields and definition_id
        """
        new_id = ObjectId()
        if root_block_key is not None:
            if block_fields is None:
                block_fields = {}
            blocks = {
                root_block_key: self._new_block(
                    user_id, root_block_key.type, block_fields, definition_id, new_id
                )
            }
        else:
            blocks = {}
        return {
            '_id': new_id,
            'root': root_block_key,
            'previous_version': None,
            'original_version': new_id,
            'edited_by': user_id,
            'edited_on': datetime.datetime.now(UTC),
            'blocks': blocks,
            'schema_version': self.SCHEMA_VERSION,
        }

    @contract(block_key=BlockKey)
    def _get_parent_from_structure(self, block_key, structure):
        """
        Given a structure, find block_key's parent in that structure. Note returns
        the encoded format for parent
        """
        for parent_block_key, value in structure['blocks'].iteritems():
            if block_key in value['fields'].get('children', []):
                return parent_block_key
        return None

    def _sync_children(self, source_parent, destination_parent, new_child):
        """
        Reorder destination's children to the same as source's and remove any no longer in source.
        Return the removed ones as orphans (a set).
        """
        destination_reordered = []
        destination_children = set(destination_parent['fields']['children'])
        source_children = source_parent['fields']['children']
        orphans = destination_children - set(source_children)
        for child in source_children:
            if child == new_child or child in destination_children:
                destination_reordered.append(child)
        destination_parent['fields']['children'] = destination_reordered
        return orphans

    @contract(
        block_key=BlockKey,
        source_blocks="dict(BlockKey: *)",
        destination_blocks="dict(BlockKey: *)",
        blacklist="list(BlockKey) | str",
    )
    def _copy_subdag(self, user_id, destination_version, block_key, source_blocks, destination_blocks, blacklist):
        """
        Update destination_blocks for the sub-dag rooted at block_key to be like the one in
        source_blocks excluding blacklist.

        Return any newly discovered orphans (as a set)
        """
        orphans = set()
        destination_block = destination_blocks.get(block_key)
        new_block = source_blocks[block_key]
        if destination_block:
            # reorder children to correspond to whatever order holds for source.
            # remove any which source no longer claims (put into orphans)
            # add any which are being copied
            source_children = new_block['fields'].get('children', [])
            existing_children = destination_block['fields'].get('children', [])
            destination_reordered = SparseList()
            for child in existing_children:
                try:
                    index = source_children.index(child)
                    destination_reordered[index] = child
                except ValueError:
                    orphans.add(BlockKey(*child))
            if blacklist != EXCLUDE_ALL:
                for index, child in enumerate(source_children):
                    if child not in blacklist:
                        destination_reordered[index] = child
            # the history of the published leaps between publications and only points to
            # previously published versions.
            previous_version = destination_block['edit_info']['update_version']
            destination_block = copy.deepcopy(new_block)
            destination_block['fields']['children'] = destination_reordered.compact_list()
            destination_block['edit_info']['previous_version'] = previous_version
            destination_block['edit_info']['update_version'] = destination_version
            destination_block['edit_info']['edited_by'] = user_id
            destination_block['edit_info']['edited_on'] = datetime.datetime.now(UTC)
        else:
            destination_block = self._new_block(
                user_id, new_block['block_type'],
                self._filter_blacklist(copy.copy(new_block['fields']), blacklist),
                new_block['definition'],
                destination_version,
                raw=True
            )

        # introduce new edit info field for tracing where copied/published blocks came
        destination_block['edit_info']['source_version'] = new_block['edit_info']['update_version']

        if blacklist != EXCLUDE_ALL:
            for child in destination_block['fields'].get('children', []):
                if child not in blacklist:
                    orphans.update(
                        self._copy_subdag(
                            user_id, destination_version, BlockKey(*child), source_blocks, destination_blocks, blacklist
                        )
                    )
        destination_blocks[block_key] = destination_block
        return orphans

    @contract(blacklist='list(BlockKey) | str')
    def _filter_blacklist(self, fields, blacklist):
        """
        Filter out blacklist from the children field in fields. Will construct a new list for children;
        so, no need to worry about copying the children field, but it will modify fiels.
        """
        if blacklist == EXCLUDE_ALL:
            fields['children'] = []
        else:
            fields['children'] = [child for child in fields.get('children', []) if BlockKey(*child) not in blacklist]
        return fields

    @contract(orphan=BlockKey)
    def _delete_if_true_orphan(self, orphan, structure):
        """
        Delete the orphan and any of its descendants which no longer have parents.
        """
        if self._get_parent_from_structure(orphan, structure) is None:
            for child in structure['blocks'][orphan]['fields'].get('children', []):
                self._delete_if_true_orphan(BlockKey(*child), structure)
            del structure['blocks'][orphan]

    def _new_block(self, user_id, category, block_fields, definition_id, new_id, raw=False):
        """
        Create the core document structure for a block.

        :param block_fields: the settings and children scoped fields as a dict or son
        :param definition_id: the pointer to the content scoped fields
        :param new_id: the structure's version id
        :param raw: true if this block already has all references serialized
        """
        if not raw:
            block_fields = self._serialize_fields(category, block_fields)
        return {
            'block_type': category,
            'definition': definition_id,
            'fields': block_fields,
            'edit_info': {
                'edited_on': datetime.datetime.now(UTC),
                'edited_by': user_id,
                'previous_version': None,
                'update_version': new_id
            }
        }

    @contract(block_key=BlockKey)
    def _get_block_from_structure(self, structure, block_key):
        """
        Encodes the block id before retrieving it from the structure to ensure it can
        be a json dict key.
        """
        return structure['blocks'].get(block_key)

    @contract(block_key=BlockKey)
    def _update_block_in_structure(self, structure, block_key, content):
        """
        Encodes the block id before accessing it in the structure to ensure it can
        be a json dict key.
        """
        structure['blocks'][block_key] = content

    def find_courses_by_search_target(self, field_name, field_value):
        """
        Find all the courses which cached that they have the given field with the given value.

        Returns: list of branch-agnostic course_keys
        """
        entries = self.find_matching_course_indexes(
            search_targets={field_name: field_value}
        )
        return [
            CourseLocator(entry['org'], entry['course'], entry['run'])  # Branch agnostic
            for entry in entries
        ]

    def get_courses_for_wiki(self, wiki_slug, **kwargs):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course keys
        """
        return self.find_courses_by_search_target('wiki_slug', wiki_slug)

    def heartbeat(self):
        """
        Check that the db is reachable.
        """
        return {ModuleStoreEnum.Type.split: self.db_connection.heartbeat()}

    def create_runtime(self, course_entry, lazy):
        """
        Create the proper runtime for this course
        """
        return CachingDescriptorSystem(
            modulestore=self,
            course_entry=course_entry,
            module_data={},
            lazy=lazy,
            default_class=self.default_class,
            error_tracker=self.error_tracker,
            render_template=self.render_template,
            mixins=self.xblock_mixins,
            select=self.xblock_select,
            services=self.services,
        )

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.

        This method is intended for use by tests and administrative commands, and not
        to be run during server startup.
        """
        self.db_connection.ensure_indexes()

class SparseList(list):
    """
    Enable inserting items into a list in arbitrary order and then retrieving them.
    """
    # taken from http://stackoverflow.com/questions/1857780/sparse-assignment-list-in-python
    def __setitem__(self, index, value):
        """
        Add value to the list ensuring the list is long enough to accommodate it at the given index
        """
        missing = index - len(self) + 1
        if missing > 0:
            self.extend([None] * missing)
        list.__setitem__(self, index, value)

    def compact_list(self):
        """
        Return as a regular lists w/ all Nones removed
        """
        return [ele for ele in self if ele is not None]
