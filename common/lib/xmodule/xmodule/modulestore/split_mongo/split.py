"""
Provides full versioning CRUD and representation for collections of xblocks (e.g., courses, modules, etc).

Representation:
* course_index: a dictionary:
    ** '_id': a unique id which cannot change,
    ** 'org': the org's id. Only used for searching not identity,
    ** 'course': the course's catalog number
    ** 'run': the course's run id or whatever user decides,
    ** 'edited_by': user_id of user who created the original entry,
    ** 'edited_on': the datetime of the original creation,
    ** 'versions': versions_dict: {branch_id: structure_id, ...}
* structure:
    ** '_id': an ObjectId (guid),
    ** 'root': root_block_id (string of key in 'blocks' for the root of this structure,
    ** 'previous_version': the structure from which this one was derived. For published courses, this
    points to the previously published version of the structure not the draft published to this.
    ** 'original_version': the original structure id in the previous_version relation. Is a pseudo object
    identifier enabling quick determination if 2 structures have any shared history,
    ** 'edited_by': user_id of the user whose change caused the creation of this structure version,
    ** 'edited_on': the datetime for the change causing this creation of this structure version,
    ** 'blocks': dictionary of xblocks in this structure:
        *** block_id: dictionary of block settings and children:
            **** 'category': the xblock type id
            **** 'definition': the db id of the record containing the content payload for this xblock
            **** 'fields': the Scope.settings and children field values
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
* definition: shared content with revision history for xblock content fields
    ** '_id': definition_id (guid),
    ** 'category': xblock type id
    ** 'fields': scope.content (and possibly other) field values.
    ** 'edit_info': dictionary:
        *** 'edited_by': user_id whose edit caused this version of the definition,
        *** 'edited_on': datetime of the change causing this version
        *** 'previous_version': the definition_id of the previous version of this definition
        *** 'original_version': definition_id of the root of the previous version relation on this
        definition. Acts as a pseudo-object identifier.
"""
import threading
import datetime
import logging
from importlib import import_module
from path import path
import copy
from pytz import UTC

from xmodule.errortracker import null_error_tracker
from opaque_keys.edx.locator import (
    BlockUsageLocator, DefinitionLocator, CourseLocator, VersionTree,
    LocalId, Locator
)
from xmodule.modulestore.exceptions import InsufficientSpecificationError, VersionConflictError, DuplicateItemError, \
    DuplicateCourseError
from xmodule.modulestore import (
    inheritance, ModuleStoreWriteBase, ModuleStoreEnum
)

from ..exceptions import ItemNotFoundError
from .definition_lazy_loader import DefinitionLazyLoader
from .caching_descriptor_system import CachingDescriptorSystem
from xblock.fields import Scope, Reference, ReferenceList, ReferenceValueDict
from bson.objectid import ObjectId
from xmodule.modulestore.split_mongo.mongo_connection import MongoConnection
from xblock.core import XBlock
from xmodule.modulestore.loc_mapper_store import LocMapperStore
from xmodule.error_module import ErrorDescriptor


log = logging.getLogger(__name__)
#==============================================================================
# Documentation is at
# https://edx-wiki.atlassian.net/wiki/display/ENG/Mongostore+Data+Structure
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
#==============================================================================


class SplitMongoModuleStore(ModuleStoreWriteBase):
    """
    A Mongodb backed ModuleStore supporting versions, inheritance,
    and sharing.
    """

    SCHEMA_VERSION = 1
    reference_type = Locator

    def __init__(self, contentstore, doc_store_config, fs_root, render_template,
                 default_class=None,
                 error_tracker=null_error_tracker,
                 loc_mapper=None,
                 i18n_service=None,
                 **kwargs):
        """
        :param doc_store_config: must have a host, db, and collection entries. Other common entries: port, tz_aware.
        """

        super(SplitMongoModuleStore, self).__init__(contentstore, **kwargs)
        self.loc_mapper = loc_mapper

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
        self.i18n_service = i18n_service

    def cache_items(self, system, base_block_ids, course_key, depth=0, lazy=True):
        '''
        Handles caching of items once inheritance and any other one time
        per course per fetch operations are done.
        :param system: a CachingDescriptorSystem
        :param base_block_ids: list of block_ids to fetch
        :param course_key: the destination course providing the context
        :param depth: how deep below these to prefetch
        :param lazy: whether to fetch definitions or use placeholders
        '''
        new_module_data = {}
        for block_id in base_block_ids:
            new_module_data = self.descendants(
                system.course_entry['structure']['blocks'],
                block_id,
                depth,
                new_module_data
            )

        if lazy:
            for block in new_module_data.itervalues():
                block['definition'] = DefinitionLazyLoader(
                    self, block['category'], block['definition'],
                    lambda fields: self.convert_references_to_keys(
                        course_key, system.load_block_type(block['category']),
                        fields, system.course_entry['structure']['blocks'],
                    )
                )
        else:
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
                        course_key, system.load_block_type(block['category']),
                        definitions[block['definition']].get('fields'),
                        system.course_entry['structure']['blocks'],
                    )
                    block['fields'].update(converted_fields)

        system.module_data.update(new_module_data)
        return system.module_data

    def _load_items(self, course_entry, block_ids, depth=0, lazy=True):
        '''
        Load & cache the given blocks from the course. Prefetch down to the
        given depth. Load the definitions into each block if lazy is False;
        otherwise, use the lazy definition placeholder.
        '''
        system = self._get_cache(course_entry['structure']['_id'])
        if system is None:
            services = {}
            if self.i18n_service:
                services["i18n"] = self.i18n_service

            system = CachingDescriptorSystem(
                modulestore=self,
                course_entry=course_entry,
                module_data={},
                lazy=lazy,
                default_class=self.default_class,
                error_tracker=self.error_tracker,
                render_template=self.render_template,
                resources_fs=None,
                mixins=self.xblock_mixins,
                select=self.xblock_select,
                services=services,
            )
            self._add_cache(course_entry['structure']['_id'], system)
            course_key = CourseLocator(
                version_guid=course_entry['structure']['_id'],
                org=course_entry.get('org'),
                course=course_entry.get('course'),
                run=course_entry.get('run'),
                branch=course_entry.get('branch'),
            )
            self.cache_items(system, block_ids, course_key, depth, lazy)
        return [system.load_item(block_id, course_entry) for block_id in block_ids]

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
            del self.thread_cache.course_cache[course_version_guid]
        else:
            self.thread_cache.course_cache = {}

    def _lookup_course(self, course_locator):
        '''
        Decode the locator into the right series of db access. Does not
        return the CourseDescriptor! It returns the actual db json from
        structures.

        Semantics: if course id and branch given, then it will get that branch. If
        also give a version_guid, it will see if the current head of that branch == that guid. If not
        it raises VersionConflictError (the version now differs from what it was when you got your
        reference)

        :param course_locator: any subclass of CourseLocator
        '''
        if course_locator.org and course_locator.course and course_locator.run and course_locator.branch:
            # use the course id
            index = self.db_connection.get_course_index(course_locator)
            if index is None:
                raise ItemNotFoundError(course_locator)
            if course_locator.branch not in index['versions']:
                raise ItemNotFoundError(course_locator)
            version_guid = index['versions'][course_locator.branch]
            if course_locator.version_guid is not None and version_guid != course_locator.version_guid:
                # This may be a bit too touchy but it's hard to infer intent
                raise VersionConflictError(course_locator, version_guid)
        elif course_locator.version_guid is None:
            raise InsufficientSpecificationError(course_locator)
        else:
            # TODO should this raise an exception if branch was provided?
            version_guid = course_locator.version_guid

        # cast string to ObjectId if necessary
        version_guid = course_locator.as_object_id(version_guid)
        entry = self.db_connection.get_structure(version_guid)

        # b/c more than one course can use same structure, the 'org', 'course',
        # 'run', and 'branch' are not intrinsic to structure
        # and the one assoc'd w/ it by another fetch may not be the one relevant to this fetch; so,
        # add it in the envelope for the structure.
        envelope = {
            'org': course_locator.org,
            'course': course_locator.course,
            'run': course_locator.run,
            'branch': course_locator.branch,
            'structure': entry,
        }
        return envelope

    def get_courses(self, branch=ModuleStoreEnum.BranchName.draft, qualifiers=None):
        '''
        Returns a list of course descriptors matching any given qualifiers.

        qualifiers should be a dict of keywords matching the db fields or any
        legal query for mongo to use against the active_versions collection.

        Note, this is to find the current head of the named branch type
        (e.g., ModuleStoreEnum.BranchName.draft). To get specific versions via guid use get_course.

        :param branch: the branch for which to return courses. Default value is ModuleStoreEnum.BranchName.draft.
        :param qualifiers: an optional dict restricting which elements should match
        '''
        if qualifiers is None:
            qualifiers = {}
        qualifiers.update({"versions.{}".format(branch): {"$exists": True}})
        matching_indexes = self.db_connection.find_matching_course_indexes(qualifiers)

        # collect ids and then query for those
        version_guids = []
        id_version_map = {}
        for course_index in matching_indexes:
            version_guid = course_index['versions'][branch]
            version_guids.append(version_guid)
            id_version_map[version_guid] = course_index

        matching_structures = self.db_connection.find_matching_structures({'_id': {'$in': version_guids}})

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
            course_list = self._load_items(envelope, [root], 0, lazy=True)
            if not isinstance(course_list[0], ErrorDescriptor):
                result.append(course_list[0])
        return result

    def get_course(self, course_id, depth=0):
        '''
        Gets the course descriptor for the course identified by the locator
        '''
        assert(isinstance(course_id, CourseLocator))
        course_entry = self._lookup_course(course_id)
        root = course_entry['structure']['root']
        result = self._load_items(course_entry, [root], 0, lazy=True)
        return result[0]

    def has_course(self, course_id, ignore_case=False):
        '''
        Does this course exist in this modulestore. This method does not verify that the branch &/or
        version in the course_id exists. Use get_course_index_info to check that.

        Returns the course_id of the course if it was found, else None
        Note: we return the course_id instead of a boolean here since the found course may have
           a different id than the given course_id when ignore_case is True.
        '''
        assert(isinstance(course_id, CourseLocator))
        course_index = self.db_connection.get_course_index(course_id, ignore_case)
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
            course_structure = self._lookup_course(usage_key)['structure']
        except ItemNotFoundError:
            # this error only occurs if the course does not exist
            return False

        return self._get_block_from_structure(course_structure, usage_key.block_id) is not None

    def has_changes(self, usage_key):
        """
        Checks if the given block has unpublished changes
        :param usage_key: the block to check
        :return: True if the draft and published versions differ
        """
        draft = self.get_item(usage_key.for_branch(ModuleStoreEnum.BranchName.draft))
        try:
            published = self.get_item(usage_key.for_branch(ModuleStoreEnum.BranchName.published))
        except ItemNotFoundError:
            return True

        return draft.update_version != published.update_version

    def get_item(self, usage_key, depth=0):
        """
        depth (int): An argument that some module stores may use to prefetch
            descendants of the queried modules for more efficient results later
            in the request. The depth is counted in the number of
            calls to get_children() to cache. None indicates to cache all
            descendants.
        raises InsufficientSpecificationError or ItemNotFoundError
        """
        assert isinstance(usage_key, BlockUsageLocator)
        course = self._lookup_course(usage_key)
        items = self._load_items(course, [usage_key.block_id], depth, lazy=True)
        if len(items) == 0:
            raise ItemNotFoundError(usage_key)
        elif len(items) > 1:
            log.debug("Found more than one item for '{}'".format(usage_key))
        return items[0]

    def get_items(self, course_locator, settings=None, content=None, **kwargs):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_locator

        NOTE: don't use this to look for courses as the course_locator is required. Use get_courses.

        Args:
            course_locator (CourseLocator): the course identifier
            settings (dict): fields to look for which have settings scope. Follows same syntax
                and rules as kwargs below
            content (dict): fields to look for which have content scope. Follows same syntax and
                rules as kwargs below.
            kwargs (key=value): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                For substring matching pass a regex object.
                For split,
                you can search by ``edited_by``, ``edited_on`` providing a function testing limits.
        """
        course = self._lookup_course(course_locator)
        items = []

        def _block_matches_all(block_json):
            """
            Check that the block matches all the criteria
            """
            # do the checks which don't require loading any additional data
            if (
                self._block_matches(block_json, kwargs) and
                self._block_matches(block_json.get('fields', {}), settings)
            ):
                if content:
                    definition_block = self.db_connection.get_definition(block_json['definition'])
                    return self._block_matches(definition_block.get('fields', {}), content)
                else:
                    return True

        if settings is None:
            settings = {}
        if 'name' in kwargs:
            # odd case where we don't search just confirm
            block_id = kwargs.pop('name')
            block = course['structure']['blocks'].get(block_id)
            if _block_matches_all(block):
                return self._load_items(course, [block_id], lazy=True)
            else:
                return []
        # don't expect caller to know that children are in fields
        if 'children' in kwargs:
            settings['children'] = kwargs.pop('children')
        for block_id, value in course['structure']['blocks'].iteritems():
            if _block_matches_all(value):
                items.append(block_id)

        if len(items) > 0:
            return self._load_items(course, items, 0, lazy=True)
        else:
            return []

    def get_parent_location(self, locator, **kwargs):
        '''
        Return the location (Locators w/ block_ids) for the parent of this location in this
        course. Could use get_items(location, {'children': block_id}) but this is slightly faster.
        NOTE: the locator must contain the block_id, and this code does not actually ensure block_id exists

        :param locator: BlockUsageLocator restricting search scope
        '''
        course = self._lookup_course(locator)
        parent_id = self._get_parent_from_structure(locator.block_id, course['structure'])
        if parent_id is None:
            return None
        return BlockUsageLocator.make_relative(
                locator,
                block_type=course['structure']['blocks'][parent_id].get('category'),
                block_id=LocMapperStore.decode_key_from_mongo(parent_id),
        )

    def get_orphans(self, course_key):
        """
        Return an array of all of the orphans in the course.
        """
        detached_categories = [name for name, __ in XBlock.load_tagged_classes("detached")]
        course = self._lookup_course(course_key)
        items = {LocMapperStore.decode_key_from_mongo(block_id) for block_id in course['structure']['blocks'].keys()}
        items.remove(course['structure']['root'])
        blocks = course['structure']['blocks']
        for block_id, block_data in blocks.iteritems():
            items.difference_update(block_data.get('fields', {}).get('children', []))
            if block_data['category'] in detached_categories:
                items.discard(LocMapperStore.decode_key_from_mongo(block_id))
        return [
            BlockUsageLocator(course_key=course_key, block_type=blocks[block_id]['category'], block_id=block_id)
            for block_id in items
        ]

    def get_course_index_info(self, course_locator):
        """
        The index records the initial creation of the indexed course and tracks the current version
        heads. This function is primarily for test verification but may serve some
        more general purpose.
        :param course_locator: must have a org, course, and run set
        :return {'org': string,
            versions: {'draft': the head draft version id,
                'published': the head published version id if any,
            },
            'edited_by': who created the course originally (named edited for consistency),
            'edited_on': when the course was originally created
        }
        """
        if not (course_locator.course and course_locator.run and course_locator.org):
            return None
        index = self.db_connection.get_course_index(course_locator)
        return index

    # TODO figure out a way to make this info accessible from the course descriptor
    def get_course_history_info(self, course_locator):
        """
        Because xblocks doesn't give a means to separate the course structure's meta information from
        the course xblock's, this method will get that info for the structure as a whole.
        :param course_locator:
        :return {'original_version': the version guid of the original version of this course,
            'previous_version': the version guid of the previous version,
            'edited_by': who made the last change,
            'edited_on': when the change was made
        }
        """
        course = self._lookup_course(course_locator)['structure']
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
        next_entries = self.db_connection.find_matching_structures({'previous_version': version_guid})
        # must only scan cursor's once
        next_versions = [struct for struct in next_entries]
        result = {version_guid: [CourseLocator(version_guid=struct['_id']) for struct in next_versions]}
        depth = 1
        while depth < version_history_depth and len(next_versions) > 0:
            depth += 1
            next_entries = self.db_connection.find_matching_structures({'previous_version':
                {'$in': [struct['_id'] for struct in next_versions]}})
            next_versions = [struct for struct in next_entries]
            for course_structure in next_versions:
                result.setdefault(course_structure['previous_version'], []).append(
                    CourseLocator(version_guid=struct['_id']))
        return VersionTree(course_locator, result)


    def get_block_generations(self, block_locator):
        '''
        Find the history of this block. Return as a VersionTree of each place the block changed (except
        deletion).

        The block's history tracks its explicit changes but not the changes in its children.

        '''
        # course_agnostic means we don't care if the head and version don't align, trust the version
        course_struct = self._lookup_course(block_locator.course_agnostic())['structure']
        block_id = block_locator.block_id
        update_version_field = 'blocks.{}.edit_info.update_version'.format(block_id)
        all_versions_with_block = self.db_connection.find_matching_structures(
            {
                'original_version': course_struct['original_version'],
                update_version_field: {'$exists': True}
            }
        )
        # find (all) root versions and build map {previous: {successors}..}
        possible_roots = []
        result = {}
        for version in all_versions_with_block:
            block_payload = self._get_block_from_structure(version, block_id)
            if version['_id'] == block_payload['edit_info']['update_version']:
                if block_payload['edit_info'].get('previous_version') is None:
                    possible_roots.append(block_payload['edit_info']['update_version'])
                else:  # map previous to {update..}
                    result.setdefault(block_payload['edit_info']['previous_version'], set()).add(
                        block_payload['edit_info']['update_version'])

        # more than one possible_root means usage was added and deleted > 1x.
        if len(possible_roots) > 1:
            # find the history segment including block_locator's version
            element_to_find = self._get_block_from_structure(course_struct, block_id)['edit_info']['update_version']
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
            "category": category,
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

        new_def_data = self._serialize_fields(old_definition['category'], new_def_data)
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
            return DefinitionLocator(old_definition['category'], old_definition['_id']), True
        else:
            return definition_locator, False

    def _generate_block_id(self, course_blocks, category):
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
        # NOTE2: this assumes category will never contain a $ nor a period.
        serial = 1
        while category + str(serial) in course_blocks:
            serial += 1
        return category + str(serial)

    # DHM: Should I rewrite this to take a new xblock instance rather than to construct it? That is, require the
    # caller to use XModuleDescriptor.load_from_json thus reducing similar code and making the object creation and
    # validation behavior a responsibility of the model layer rather than the persistence layer.
    def create_item(
        self, course_or_parent_locator, category, user_id,
        block_id=None, definition_locator=None, fields=None,
        force=False, continue_version=False
    ):
        """
        Add a descriptor to persistence as the last child of the optional parent_location or just as an element
        of the course (if no parent provided). Return the resulting post saved version with populated locators.

        :param course_or_parent_locator: If BlockUsageLocator, then it's assumed to be the parent.
        If it's a CourseLocator, then it's
        merely the containing course. If it has a version_guid and a course org + course + run + branch, this
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

        :param continue_version: continue changing the current structure at the head of the course. Very dangerous
        unless used in the same request as started the change! See below about version conflicts.

        This method creates a new version of the course structure unless continue_version is True.
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
        # find course_index entry if applicable and structures entry
        index_entry = self._get_index_if_valid(course_or_parent_locator, force, continue_version)
        structure = self._lookup_course(course_or_parent_locator)['structure']

        partitioned_fields = self.partition_fields_by_scope(category, fields)
        new_def_data = partitioned_fields.get(Scope.content, {})
        # persist the definition if persisted != passed
        if (definition_locator is None or isinstance(definition_locator.definition_id, LocalId)):
            definition_locator = self.create_definition_from_data(new_def_data, category, user_id)
        elif new_def_data is not None:
            definition_locator, _ = self.update_definition_from_data(definition_locator, new_def_data, user_id)

        # copy the structure and modify the new one
        if continue_version:
            new_structure = structure
        else:
            new_structure = self._version_structure(structure, user_id)

        new_id = new_structure['_id']

        # generate usage id
        if block_id is not None:
            if LocMapperStore.encode_key_for_mongo(block_id) in new_structure['blocks']:
                raise DuplicateItemError(block_id, self, 'structures')
            else:
                new_block_id = block_id
        else:
            new_block_id = self._generate_block_id(new_structure['blocks'], category)

        block_fields = partitioned_fields.get(Scope.settings, {})
        if Scope.children in partitioned_fields:
            block_fields.update(partitioned_fields[Scope.children])
        self._update_block_in_structure(new_structure, new_block_id, {
            "category": category,
            "definition": definition_locator.definition_id,
            "fields": self._serialize_fields(category, block_fields),
            'edit_info': {
                'edited_on': datetime.datetime.now(UTC),
                'edited_by': user_id,
                'previous_version': None,
                'update_version': new_id,
            }
        })

        # if given parent, add new block as child and update parent's version
        parent = None
        if isinstance(course_or_parent_locator, BlockUsageLocator) and course_or_parent_locator.block_id is not None:
            encoded_block_id = LocMapperStore.encode_key_for_mongo(course_or_parent_locator.block_id)
            parent = new_structure['blocks'][encoded_block_id]
            parent['fields'].setdefault('children', []).append(new_block_id)
            if not continue_version or parent['edit_info']['update_version'] != structure['_id']:
                parent['edit_info']['edited_on'] = datetime.datetime.now(UTC)
                parent['edit_info']['edited_by'] = user_id
                parent['edit_info']['previous_version'] = parent['edit_info']['update_version']
                parent['edit_info']['update_version'] = new_id
        if continue_version:
            # db update
            self.db_connection.update_structure(new_structure)
            # clear cache so things get refetched and inheritance recomputed
            self._clear_cache(new_id)
        else:
            self.db_connection.insert_structure(new_structure)

        # update the index entry if appropriate
        if index_entry is not None:
            if not continue_version:
                self._update_head(index_entry, course_or_parent_locator.branch, new_id)
            item_loc = BlockUsageLocator(
                course_or_parent_locator.version_agnostic(),
                block_type=category,
                block_id=new_block_id,
            )
        else:
            item_loc = BlockUsageLocator(
                CourseLocator(version_guid=new_id),
                block_type=category,
                block_id=new_block_id,
            )

        # reconstruct the new_item from the cache
        return self.get_item(item_loc)

    def clone_course(self, source_course_id, dest_course_id, user_id):
        """
        See :meth: `.ModuleStoreWrite.clone_course` for documentation.

        In split, other than copying the assets, this is cheap as it merely creates a new version of the
        existing course.
        """
        super(SplitMongoModuleStore, self).clone_course(source_course_id, dest_course_id, user_id)
        source_index = self.get_course_index_info(source_course_id)
        return self.create_course(
            dest_course_id.org, dest_course_id.offering, user_id, fields=None,  # override start_date?
            versions_dict=source_index['versions']
        )

    def create_course(
        self, org, course, run, user_id, fields=None,
        master_branch=ModuleStoreEnum.BranchName.draft, versions_dict=None, root_category='course',
        root_block_id='course', **kwargs
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

        versions_dict: the starting version ids where the keys are the tags such as DRAFT and PUBLISHED
        and the values are structure guids. If provided, the new course will reuse this version (unless you also
        provide any fields overrides, see above). if not provided, will create a mostly empty course
        structure with just a category course root xblock.
        """
        # check course and run's uniqueness
        locator = CourseLocator(org=org, course=course, run=run, branch=master_branch)
        index = self.db_connection.get_course_index(locator)
        if index is not None:
            raise DuplicateCourseError(locator, index)

        partitioned_fields = self.partition_fields_by_scope(root_category, fields)
        block_fields = partitioned_fields.setdefault(Scope.settings, {})
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
                'category': root_category,
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
                user_id, root_block_id, root_category, block_fields, definition_id
            )
            new_id = draft_structure['_id']

            self.db_connection.insert_structure(draft_structure)

            if versions_dict is None:
                versions_dict = {master_branch: new_id}
            else:
                versions_dict[master_branch] = new_id

        else:
            # just get the draft_version structure
            draft_version = CourseLocator(version_guid=versions_dict[master_branch])
            draft_structure = self._lookup_course(draft_version)['structure']
            if definition_fields or block_fields:
                draft_structure = self._version_structure(draft_structure, user_id)
                new_id = draft_structure['_id']
                encoded_block_id = LocMapperStore.encode_key_for_mongo(draft_structure['root'])
                root_block = draft_structure['blocks'][encoded_block_id]
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

                self.db_connection.insert_structure(draft_structure)
                versions_dict[master_branch] = new_id

        index_entry = {
            '_id': ObjectId(),
            'org': org,
            'course': course,
            'run': run,
            'edited_by': user_id,
            'edited_on': datetime.datetime.now(UTC),
            'versions': versions_dict,
            'schema_version': self.SCHEMA_VERSION,
        }
        self.db_connection.insert_course_index(index_entry)
        return self.get_course(locator)

    def update_item(self, descriptor, user_id, allow_not_found=False, force=False):
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
        original_structure = self._lookup_course(descriptor.location)['structure']
        index_entry = self._get_index_if_valid(descriptor.location, force)

        descriptor.definition_locator, is_updated = self.update_definition_from_data(
            descriptor.definition_locator, descriptor.get_explicitly_set_fields_by_scope(Scope.content), user_id)

        original_entry = self._get_block_from_structure(original_structure, descriptor.location.block_id)
        # check metadata
        settings = descriptor.get_explicitly_set_fields_by_scope(Scope.settings)
        settings = self._serialize_fields(descriptor.category, settings)
        if not is_updated:
            is_updated = self._compare_settings(settings, original_entry['fields'])

        # check children
        if descriptor.has_children:
            serialized_children = [child.block_id for child in descriptor.children]
            is_updated = is_updated or original_entry['fields'].get('children', []) != serialized_children
            if is_updated:
                settings['children'] = serialized_children

        # if updated, rev the structure
        if is_updated:
            new_structure = self._version_structure(original_structure, user_id)
            block_data = self._get_block_from_structure(new_structure, descriptor.location.block_id)

            block_data["definition"] = descriptor.definition_locator.definition_id
            block_data["fields"] = settings

            new_id = new_structure['_id']
            block_data['edit_info'] = {
                'edited_on': datetime.datetime.now(UTC),
                'edited_by': user_id,
                'previous_version': block_data['edit_info']['update_version'],
                'update_version': new_id,
            }
            self.db_connection.insert_structure(new_structure)
            # update the index entry if appropriate
            if index_entry is not None:
                self._update_head(index_entry, descriptor.location.branch, new_id)
                course_key = CourseLocator(
                    org=index_entry['org'],
                    course=index_entry['course'],
                    run=index_entry['run'],
                    branch=descriptor.location.branch,
                    version_guid=new_id
                )
            else:
                course_key = CourseLocator(version_guid=new_id)

            # fetch and return the new item--fetching is unnecessary but a good qc step
            new_locator = descriptor.location.map_into_course(course_key)
            return self.get_item(new_locator)
        else:
            # nothing changed, just return the one sent in
            return descriptor

    def create_xblock(self, runtime, category, fields=None, block_id=None, definition_id=None, parent_xblock=None):
        """
        This method instantiates the correct subclass of XModuleDescriptor based
        on the contents of json_data. It does not persist it and can create one which
        has no usage id.

        parent_xblock is used to compute inherited metadata as well as to append the new xblock.

        json_data:
        - 'category': the xmodule category
        - 'fields': a dict of locally set fields (not inherited) in json format not pythonic typed format!
        - 'definition': the object id of the existing definition
        """
        xblock_class = runtime.load_block_type(category)
        json_data = {
            'category': category,
            'fields': fields or {},
        }
        if definition_id is not None:
            json_data['definition'] = definition_id
        if parent_xblock is not None:
            json_data['_inherited_settings'] = parent_xblock.xblock_kvs.inherited_settings.copy()
            if fields is not None:
                for field_name in inheritance.InheritanceMixin.fields:
                    if field_name in fields:
                        json_data['_inherited_settings'][field_name] = fields[field_name]

        new_block = runtime.xblock_from_json(xblock_class, block_id, json_data)
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
        index_entry = self._get_index_if_valid(xblock.location, force)
        structure = self._lookup_course(xblock.location)['structure']
        new_structure = self._version_structure(structure, user_id)
        new_id = new_structure['_id']
        is_updated = self._persist_subdag(xblock, user_id, new_structure['blocks'], new_id)

        if is_updated:
            self.db_connection.insert_structure(new_structure)

            # update the index entry if appropriate
            if index_entry is not None:
                self._update_head(index_entry, xblock.location.branch, new_id)

            # fetch and return the new item--fetching is unnecessary but a good qc step
            return self.get_item(xblock.location.for_version(new_id))
        else:
            return xblock

    def _persist_subdag(self, xblock, user_id, structure_blocks, new_id):
        # persist the definition if persisted != passed
        new_def_data = self._serialize_fields(xblock.category, xblock.get_explicitly_set_fields_by_scope(Scope.content))
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
                block_id = self._generate_block_id(structure_blocks, xblock.category)
            encoded_block_id = LocMapperStore.encode_key_for_mongo(block_id)
            new_usage_id = xblock.scope_ids.usage_id.replace(block_id=block_id)
            xblock.scope_ids = xblock.scope_ids._replace(usage_id=new_usage_id)  # pylint: disable=protected-access
        else:
            is_new = False
            encoded_block_id = LocMapperStore.encode_key_for_mongo(xblock.location.block_id)

        children = []
        if xblock.has_children:
            for child in xblock.children:
                if isinstance(child.block_id, LocalId):
                    child_block = xblock.system.get_block(child)
                    is_updated = self._persist_subdag(child_block, user_id, structure_blocks, new_id) or is_updated
                    children.append(child_block.location.block_id)
                else:
                    children.append(child.block_id)
            is_updated = is_updated or structure_blocks[encoded_block_id]['fields']['children'] != children

        block_fields = xblock.get_explicitly_set_fields_by_scope(Scope.settings)
        block_fields = self._serialize_fields(xblock.category, block_fields)
        if not is_new and not is_updated:
            is_updated = self._compare_settings(block_fields, structure_blocks[encoded_block_id]['fields'])
        if children:
            block_fields['children'] = children

        if is_updated:
            previous_version = None if is_new else structure_blocks[encoded_block_id]['edit_info'].get('update_version')
            structure_blocks[encoded_block_id] = {
                "category": xblock.category,
                "definition": xblock.definition_locator.definition_id,
                "fields": block_fields,
                'edit_info': {
                    'previous_version': previous_version,
                    'update_version': new_id,
                    'edited_by': user_id,
                    'edited_on': datetime.datetime.now(UTC)
                }
            }

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

    def xblock_publish(self, user_id, source_course, destination_course, subtree_list, blacklist):
        """
        Publishes each xblock in subtree_list and those blocks descendants excluding blacklist
        from source_course to destination_course.

        To delete a block, publish its parent. You can blacklist the other sibs to keep them from
        being refreshed. You can also just call delete_item on the destination.

        To unpublish a block, call delete_item on the destination.

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
        source_structure = self._lookup_course(source_course)['structure']
        index_entry = self.db_connection.get_course_index(destination_course)
        if index_entry is None:
            # brand new course
            raise ItemNotFoundError(destination_course)
        if destination_course.branch not in index_entry['versions']:
            # must be publishing the dag root if there's no current dag
            root_block_id = source_structure['root']
            if not any(root_block_id == subtree.block_id for subtree in subtree_list):
                raise ItemNotFoundError(u'Must publish course root {}'.format(root_block_id))
            # create branch
            destination_structure = self._new_structure(user_id, root_block_id)
        else:
            destination_structure = self._lookup_course(destination_course)['structure']
            destination_structure = self._version_structure(destination_structure, user_id)

        blacklist = [shunned.block_id for shunned in blacklist or []]
        # iterate over subtree list filtering out blacklist.
        orphans = set()
        destination_blocks = destination_structure['blocks']
        for subtree_root in subtree_list:
            if subtree_root.block_id != source_structure['root']:
                # find the parents and put root in the right sequence
                parent = self._get_parent_from_structure(subtree_root.block_id, source_structure)
                if parent is not None:  # may be a detached category xblock
                    if not parent in destination_blocks:
                        raise ItemNotFoundError(parent)
                    orphans.update(
                        self._sync_children(
                            source_structure['blocks'][parent],
                            destination_blocks[parent],
                            subtree_root.block_id
                        )
                    )
            # update/create the subtree and its children in destination (skipping blacklist)
            orphans.update(
                self._publish_subdag(
                    user_id, subtree_root.block_id, source_structure['blocks'], destination_blocks, blacklist
                )
            )
        # remove any remaining orphans
        for orphan in orphans:
            # orphans will include moved as well as deleted xblocks. Only delete the deleted ones.
            self._delete_if_true_orphan(orphan, destination_structure)

        # update the db
        self.db_connection.insert_structure(destination_structure)
        self._update_head(index_entry, destination_course.branch, destination_structure['_id'])

    def unpublish(self, location, user_id):
        published_location = location.replace(branch=ModuleStoreEnum.BranchName.published)
        self.delete_item(published_location, user_id)

    def update_course_index(self, updated_index_entry):
        """
        Change the given course's index entry.

        Note, this operation can be dangerous and break running courses.

        Does not return anything useful.
        """
        self.db_connection.update_course_index(updated_index_entry)

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
        assert isinstance(usage_locator, BlockUsageLocator)
        original_structure = self._lookup_course(usage_locator.course_key)['structure']
        if original_structure['root'] == usage_locator.block_id:
            raise ValueError("Cannot delete the root of a course")
        index_entry = self._get_index_if_valid(usage_locator, force)
        new_structure = self._version_structure(original_structure, user_id)
        new_blocks = new_structure['blocks']
        new_id = new_structure['_id']
        encoded_block_id = self._get_parent_from_structure(usage_locator.block_id, original_structure)
        parent_block = new_blocks[encoded_block_id]
        parent_block['fields']['children'].remove(usage_locator.block_id)
        parent_block['edit_info']['edited_on'] = datetime.datetime.now(UTC)
        parent_block['edit_info']['edited_by'] = user_id
        parent_block['edit_info']['previous_version'] = parent_block['edit_info']['update_version']
        parent_block['edit_info']['update_version'] = new_id

        def remove_subtree(block_id):
            """
            Remove the subtree rooted at block_id
            """
            encoded_block_id = LocMapperStore.encode_key_for_mongo(block_id)
            for child in new_blocks[encoded_block_id]['fields'].get('children', []):
                remove_subtree(child)
            del new_blocks[encoded_block_id]

        remove_subtree(usage_locator.block_id)

        # update index if appropriate and structures
        self.db_connection.insert_structure(new_structure)

        if index_entry is not None:
            # update the index entry if appropriate
            self._update_head(index_entry, usage_locator.branch, new_id)
            result = usage_locator.course_key.for_version(new_id)
        else:
            result = CourseLocator(version_guid=new_id)

        return result

    def delete_course(self, course_key, user_id):
        """
        Remove the given course from the course index.

        Only removes the course from the index. The data remains. You can use create_course
        with a versions hash to restore the course; however, the edited_on and
        edited_by won't reflect the originals, of course.
        """
        index = self.db_connection.get_course_index(course_key)
        if index is None:
            raise ItemNotFoundError(course_key)
        # this is the only real delete in the system. should it do something else?
        log.info(u"deleting course from split-mongo: %s", course_key)
        self.db_connection.delete_course_index(index)

        # We do NOT call the super class here since we need to keep the assets
        # in case the course is later restored.
        # super(SplitMongoModuleStore, self).delete_course(course_key, user_id)

    def revert_to_published(self, location, user_id=None):
        """
        Reverts an item to its last published version (recursively traversing all of its descendants).
        If no published version exists, a VersionConflictError is thrown.

        If a published version exists but there is no draft version of this item or any of its descendants, this
        method is a no-op.

        :raises InvalidVersionError: if no published version exists for the location specified
        """
        raise NotImplementedError()

    def inherit_settings(self, block_map, block_json, inheriting_settings=None):
        """
        Updates block_json with any inheritable setting set by an ancestor and recurses to children.
        """
        if block_json is None:
            return

        if inheriting_settings is None:
            inheriting_settings = {}

        # the currently passed down values take precedence over any previously cached ones
        # NOTE: this should show the values which all fields would have if inherited: i.e.,
        # not set to the locally defined value but to value set by nearest ancestor who sets it
        # ALSO NOTE: no xblock should ever define a _inherited_settings field as it will collide w/ this logic.
        block_json.setdefault('_inherited_settings', {}).update(inheriting_settings)

        # update the inheriting w/ what should pass to children
        inheriting_settings = block_json['_inherited_settings'].copy()
        block_fields = block_json['fields']
        for field_name in inheritance.InheritanceMixin.fields:
            if field_name in block_fields:
                inheriting_settings[field_name] = block_fields[field_name]

        for child in block_fields.get('children', []):
            try:
                child = LocMapperStore.encode_key_for_mongo(child)
                self.inherit_settings(block_map, block_map[child], inheriting_settings)
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
        encoded_block_id = LocMapperStore.encode_key_for_mongo(block_id)
        if encoded_block_id not in block_map:
            return descendent_map

        if block_id not in descendent_map:
            descendent_map[block_id] = block_map[encoded_block_id]

        if depth is None or depth > 0:
            depth = depth - 1 if depth is not None else None
            for child in descendent_map[block_id]['fields'].get('children', []):
                descendent_map = self.descendants(block_map, child, depth,
                    descendent_map)

        return descendent_map

    def definition_locator(self, definition):
        '''
        Pull the id out of the definition w/ correct semantics for its
        representation
        '''
        if isinstance(definition, DefinitionLazyLoader):
            return definition.definition_locator
        elif '_id' not in definition:
            return DefinitionLocator(definition.get('category'), LocalId())
        else:
            return DefinitionLocator(definition['category'], definition['_id'])

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
                    if LocMapperStore.encode_key_for_mongo(block_id) in original_structure['blocks']
                ]
        self.db_connection.update_structure(original_structure)
        # clear cache again b/c inheritance may be wrong over orphans
        self._clear_cache(original_structure['_id'])

    def convert_references_to_keys(self, course_key, xblock_class, jsonfields, blocks):
        """
        Convert the given serialized fields to the deserialized values by finding all references
        and converting them.
        :param jsonfields: the serialized copy of the xblock's fields
        """
        def robust_usage_key(block_id):
            """
            create a course_key relative usage key for the block_id. If the block_id is in blocks,
            use its correct category; otherwise, use 'unknown'.
            The purpose for this is that some operations add pointers as they build up the
            structure without worrying about order of creation. Because the category of the
            usage_key is for the most part inert, it's better to hack a value than to work
            out a dependency graph algorithm for those functions which may prereference blocks.
            """
            # if this was taken from cache, then its fields are already converted
            if isinstance(block_id, BlockUsageLocator):
                return block_id
            try:
                return course_key.make_usage_key(
                    blocks[LocMapperStore.encode_key_for_mongo(block_id)]['category'], block_id
                )
            except KeyError:
                return course_key.make_usage_key('unknown', block_id)

        xblock_class = self.mixologist.mix(xblock_class)
        for field_name, value in jsonfields.iteritems():
            if value:
                field = xblock_class.fields.get(field_name)
                if field is None:
                    continue
                elif isinstance(field, Reference):
                    jsonfields[field_name] = robust_usage_key(value)
                elif isinstance(field, ReferenceList):
                    jsonfields[field_name] = [robust_usage_key(ele) for ele in value]
                elif isinstance(field, ReferenceValueDict):
                    for key, subvalue in value.iteritems():
                        assert isinstance(subvalue, basestring)
                        value[key] = robust_usage_key(subvalue)
        return jsonfields

    def _get_index_if_valid(self, locator, force=False, continue_version=False):
        """
        If the locator identifies a course and points to its draft (or plausibly its draft),
        then return the index entry.

        raises VersionConflictError if not the right version

        :param locator: a courselocator
        :param force: if false, raises VersionConflictError if the current head of the course != the one identified
        by locator. Cannot be True if continue_version is True
        :param continue_version: if True, assumes this operation requires a head version and will not create a new
        version but instead continue an existing transaction on this version. This flag cannot be True if force is True.
        """
        if locator.org is None or locator.course is None or locator. run is None or locator.branch is None:
            if continue_version:
                raise InsufficientSpecificationError(
                    "To continue a version, the locator must point to one ({}).".format(locator)
                )
            else:
                return None
        else:
            index_entry = self.db_connection.get_course_index(locator)
            is_head = (
                locator.version_guid is None or
                index_entry['versions'][locator.branch] == locator.version_guid
            )
            if (is_head or (force and not continue_version)):
                return index_entry
            else:
                raise VersionConflictError(
                    locator,
                    index_entry['versions'][locator.branch]
                )

    def _version_structure(self, structure, user_id):
        """
        Copy the structure and update the history info (edited_by, edited_on, previous_version)
        :param structure:
        :param user_id:
        """
        new_structure = copy.deepcopy(structure)
        new_structure['_id'] = ObjectId()
        new_structure['previous_version'] = structure['_id']
        new_structure['edited_by'] = user_id
        new_structure['edited_on'] = datetime.datetime.now(UTC)
        new_structure['schema_version'] = self.SCHEMA_VERSION
        return new_structure

    def _find_local_root(self, element_to_find, possibility, tree):
        if possibility not in tree:
            return False
        if element_to_find in tree[possibility]:
            return True
        for subtree in tree[possibility]:
            if self._find_local_root(element_to_find, subtree, tree):
                return True
        return False


    def _update_head(self, index_entry, branch, new_id):
        """
        Update the active index for the given course's branch to point to new_id

        :param index_entry:
        :param course_locator:
        :param new_id:
        """
        index_entry['versions'][branch] = new_id
        self.db_connection.update_course_index(index_entry)

    def _serialize_fields(self, category, fields):
        """
        Convert any references to their serialized form.

        Remove any fields which split or its kvs computes or adds but does not want persisted.

        :param fields: a dict of fields
        """
        assert isinstance(fields, dict)
        xblock_class = XBlock.load_class(category, self.default_class)
        xblock_class = self.mixologist.mix(xblock_class)
        for field_name, value in fields.iteritems():
            if value:
                if isinstance(xblock_class.fields[field_name], Reference):
                    fields[field_name] = value.block_id
                elif isinstance(xblock_class.fields[field_name], ReferenceList):
                    fields[field_name] = [
                        ele.block_id for ele in value
                    ]
                elif isinstance(xblock_class.fields[field_name], ReferenceValueDict):
                    for key, subvalue in value.iteritems():
                        assert isinstance(subvalue, Location)
                        value[key] = subvalue.block_id

        # I think these are obsolete conditions; so, I want to confirm that. Thus the warnings
        if 'location' in fields:
            log.warn('attempt to persist location')
            del fields['location']
        if 'category' in fields:
            log.warn('attempt to persist category')
            del fields['category']
        return fields

    def _new_structure(self, user_id, root_block_id,
                       root_category=None, block_fields=None, definition_id=None):
        """
        Internal function: create a structure element with no previous version. Must provide the root id
        but not necessarily the info needed to create it (for the use case of publishing). If providing
        root_category, must also provide block_fields and definition_id
        """
        new_id = ObjectId()
        if root_category is not None:
            encoded_root = LocMapperStore.encode_key_for_mongo(root_block_id)
            blocks = {
                encoded_root: self._new_block(
                    user_id, root_category, block_fields, definition_id, new_id
                )
            }
        else:
            blocks = {}
        return {
            '_id': new_id,
            'root': root_block_id,
            'previous_version': None,
            'original_version': new_id,
            'edited_by': user_id,
            'edited_on': datetime.datetime.now(UTC),
            'blocks': blocks,
            'schema_version': self.SCHEMA_VERSION,
        }

    def _get_parent_from_structure(self, block_id, structure):
        """
        Given a structure, find block_id's parent in that structure. Note returns
        the encoded format for parent
        """
        for parent_id, value in structure['blocks'].iteritems():
            for child_id in value['fields'].get('children', []):
                if block_id == child_id:
                    return parent_id
        return None

    def _sync_children(self, source_parent, destination_parent, new_child):
        """
        Reorder destination's children to the same as source's and remove any no longer in source.
        Return the removed ones as orphans (a set).
        """
        destination_reordered = []
        destination_children = destination_parent['fields']['children']
        source_children = source_parent['fields']['children']
        orphans = set()
        for child in destination_children:
            try:
                source_children.index(child)
            except ValueError:
                orphans.add(child)
        for child in source_children:
            if child == new_child or child in destination_children:
                destination_reordered.append(child)
        destination_parent['fields']['children'] = destination_reordered
        return orphans

    def _publish_subdag(self, user_id, block_id, source_blocks, destination_blocks, blacklist):
        """
        Update destination_blocks for the sub-dag rooted at block_id to be like the one in
        source_blocks excluding blacklist.

        Return any newly discovered orphans (as a set)
        """
        orphans = set()
        encoded_block_id = LocMapperStore.encode_key_for_mongo(block_id)
        destination_block = destination_blocks.get(encoded_block_id)
        new_block = source_blocks[encoded_block_id]
        if destination_block:
            if destination_block['edit_info']['update_version'] != new_block['edit_info']['update_version']:
                source_children = new_block['fields']['children']
                for child in destination_block['fields']['children']:
                    try:
                        source_children.index(child)
                    except ValueError:
                        orphans.add(child)
                previous_version = new_block['edit_info']['update_version']
                destination_block = copy.deepcopy(new_block)
                destination_block['fields'] = self._filter_blacklist(destination_block['fields'], blacklist)
                destination_block['edit_info']['previous_version'] = previous_version
                destination_block['edit_info']['edited_by'] = user_id
        else:
            destination_block = self._new_block(
                user_id, new_block['category'],
                self._filter_blacklist(copy.copy(new_block['fields']), blacklist),
                new_block['definition'],
                new_block['edit_info']['update_version'],
                raw=True
            )
        for child in destination_block['fields'].get('children', []):
            if child not in blacklist:
                orphans.update(self._publish_subdag(user_id, child, source_blocks, destination_blocks, blacklist))
        destination_blocks[encoded_block_id] = destination_block
        return orphans

    def _filter_blacklist(self, fields, blacklist):
        """
        Filter out blacklist from the children field in fields. Will construct a new list for children;
        so, no need to worry about copying the children field, but it will modify fiels.
        """
        fields['children'] = [child for child in fields.get('children', []) if child not in blacklist]
        return fields

    def _delete_if_true_orphan(self, orphan, structure):
        """
        Delete the orphan and any of its descendants which no longer have parents.
        """
        if self._get_parent_from_structure(orphan, structure) is None:
            encoded_block_id = LocMapperStore.encode_key_for_mongo(orphan)
            for child in structure['blocks'][encoded_block_id]['fields'].get('children', []):
                self._delete_if_true_orphan(child, structure)
            del structure['blocks'][encoded_block_id]

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
            'category': category,
            'definition': definition_id,
            'fields': block_fields,
            'edit_info': {
                'edited_on': datetime.datetime.now(UTC),
                'edited_by': user_id,
                'previous_version': None,
                'update_version': new_id
            }
        }

    def _get_block_from_structure(self, structure, block_id):
        """
        Encodes the block id before retrieving it from the structure to ensure it can
        be a json dict key.
        """
        return structure['blocks'].get(LocMapperStore.encode_key_for_mongo(block_id))

    def _update_block_in_structure(self, structure, block_id, content):
        """
        Encodes the block id before accessing it in the structure to ensure it can
        be a json dict key.
        """
        structure['blocks'][LocMapperStore.encode_key_for_mongo(block_id)] = content

    def get_courses_for_wiki(self, wiki_slug):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course locations

        Todo: Needs to be implemented.
        """
        courses = []
        return courses

    def heartbeat(self):
        """
        Check that the db is reachable.
        """
        return {ModuleStoreEnum.Type.split: self.db_connection.heartbeat()}

    def compute_publish_state(self, xblock):
        """
        Returns whether this xblock is draft, public, or private.

        Returns:
            PublishState.draft - content is in the process of being edited, but still has a previous
                version deployed to LMS
            PublishState.public - content is locked and deployed to LMS
            PublishState.private - content is editable and not deployed to LMS
        """
        # TODO implement
        raise NotImplementedError()

    def convert_to_draft(self, location, user_id):
        """
        Create a copy of the source and mark its revision as draft.

        :param source: the location of the source (its revision must be None)
        """
        # This is a no-op in Split since a draft version of the data always remains
        pass
