from . import ModuleStoreBase
from .exceptions import ItemNotFoundError, DuplicateItemError
from importlib import import_module
from path import path
from xmodule.course_module import CourseDescriptor
from xmodule.error_module import ErrorDescriptor
from xmodule.errortracker import null_error_tracker, exc_info_to_str
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.x_module import XModuleDescriptor
import logging
import pymongo
import sys
from xmodule.modulestore.locator import BlockUsageLocator, DescriptionLocator, CourseLocator, VersionTree
from xblock.runtime import DbModel, KeyValueStore, InvalidScopeError
from collections import namedtuple
from xblock.core import Scope
from xmodule.modulestore.exceptions import InsufficientSpecificationError, NotDraftVersion, VersionConflictError
import re
from xmodule.modulestore import inheritance
import threading
import datetime
import copy


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


# id is a BlockUsageLocator, def_id is the definition's guid
SplitMongoKVSid = namedtuple('SplitMongoKVSid', 'id, def_id')


# TODO should this be here or w/ x_module or ???
class DefinitionLazyLoader(object):
    '''
    A placeholder to put into an xblock in place of its definition which
    when accessed knows how to get its content. Only useful if the containing
    object doesn't force access during init but waits until client wants the
    definition. Only works if the modulestore is a split mongo store.
    '''
    def __init__(self, modulestore, definition_id):
        '''
        Simple placeholder for yet-to-be-fetched data
        :param modulestore: the pymongo db connection with the definitions
        :param definition_locator: the id of the record in the above to fetch
        '''
        self.modulestore = modulestore
        self.definition_locator = DescriptionLocator(definition_id)

    def fetch(self):
        '''
        Fetch the definition. Note, the caller should replace this lazy
        loader pointer with the result so as not to fetch more than once
        '''
        return self.modulestore.definitions.find_one(
            {'_id': self.definition_locator.def_id})


# TODO should this be here or w/ x_module or ???
class SplitMongoKVS(KeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """
    def __init__(self, definition, children, metadata, _inherited_metadata):
        """

        :param definition:
        :param children:
        :param metadata: the locally defined value for each metadata field
        :param _inherited_metadata: the value of each inheritable field from above this.
            Note, metadata may override and disagree w/ this b/c this says what the value
            should be if metadata is undefined for this field.
        """
        # ensure kvs's don't share objects w/ others so that changes can't appear in separate ones
        # the particular use case was that changes to kvs's were polluting caches. My thinking was
        # that kvs's should be independent thus responsible for the isolation.
        if isinstance(definition, DefinitionLazyLoader):
            self._definition = definition
        else:
            self._definition = copy.copy(definition)
        self._children = copy.copy(children)
        self._metadata = copy.copy(metadata)
        self._inherited_metadata = _inherited_metadata

    def get(self, key):
        if key.scope == Scope.children:
            return self._children
        elif key.scope == Scope.parent:
            return None
        elif key.scope == Scope.settings:
            if key.field_name in self._metadata:
                value = self._metadata[key.field_name]
            elif key.field_name in self._inherited_metadata:
                value = self._inherited_metadata[key.field_name]
            else:
                raise KeyError()
            return value
        elif key.scope == Scope.content:
            if isinstance(self._definition, DefinitionLazyLoader):
                self._definition = self._definition.fetch()
            if (key.field_name == 'data' and
                not isinstance(self._definition.get('data'), dict)):
                return self._definition.get('data')
            elif key.field_name in SplitMongoModuleStore.VERSION_FIELDS:
                return self._definition[key.field_name]
            elif 'data' not in self._definition or key.field_name not in self._definition['data']:
                raise KeyError()
            else:
                return self._definition['data'][key.field_name]
        else:
            raise InvalidScopeError(key.scope)

    def set(self, key, value):
        # TODO cache db update implications & add method to invoke
        if key.scope == Scope.children:
            self._children = value
            # TODO remove inheritance from any orphaned exchildren
            # TODO add inheritance to any new children
        elif key.scope == Scope.settings:
            # TODO if inheritable, push down to children who don't override
            self._metadata[key.field_name] = value
        elif key.scope == Scope.content:
            if isinstance(self._definition, DefinitionLazyLoader):
                self._definition = self._definition.fetch()
            if (key.field_name == 'data' and
                not isinstance(self._definition.get('data'), dict)):
                self._definition.get('data')
            elif key.field_name in SplitMongoModuleStore.VERSION_FIELDS:
                self._definition[key.field_name] = value
            else:
                self._definition.setdefault('data', {})[key.field_name] = value
        else:
            raise InvalidScopeError(key.scope)

    def delete(self, key):
        # TODO cache db update implications & add method to invoke
        if key.scope == Scope.children:
            self._children = []
        elif key.scope == Scope.settings:
            # TODO if inheritable, ensure _inherited_metadata has value from above and
            # revert children to that value
            if key.field_name in self._metadata:
                del self._metadata[key.field_name]
        elif key.scope == Scope.content:
            if isinstance(self._definition, DefinitionLazyLoader):
                self._definition = self._definition.fetch()
            if (key.field_name == 'data' and
                not isinstance(self._definition.get('data'), dict)):
                self._definition.setdefault('data', None)
            # no delete for the system version fields: should this throw error?
            elif key.field_name in SplitMongoModuleStore.VERSION_FIELDS:
                pass
            else:
                try:
                    del self._definition['data'][key.field_name]
                except KeyError:
                    pass
        else:
            raise InvalidScopeError(key.scope)

    def has(self, key):
        if key.scope in (Scope.children, Scope.parent):
            return True
        elif key.scope == Scope.settings:
            return key.field_name in self._metadata or key.field_name in self._inherited_metadata
        elif key.scope == Scope.content:
            if isinstance(self._definition, DefinitionLazyLoader):
                self._definition = self._definition.fetch()
            if (key.field_name == 'data' and
                not isinstance(self._definition.get('data'), dict)):
                return self._definition.get('data') is not None
            elif key.field_name in SplitMongoModuleStore.VERSION_FIELDS:
                return key.field_name in self._definition
            else:
                return key.field_name in self._definition.get('data', {})
        else:
            return False

    def get_data(self):
        """
        Intended only for use by persistence layer to get the native definition['data'] rep
        """
        if isinstance(self._definition, DefinitionLazyLoader):
            self._definition = self._definition.fetch()
        return self._definition.get('data')

    def get_own_metadata(self):
        """
        Get the metadata explicitly set on this element.
        """
        return self._metadata

    def get_inherited_metadata(self):
        """
        Get the metadata set by the ancestors (which own metadata may override or not)
        """
        return self._inherited_metadata


# TODO should this be here or w/ x_module or ???
class CachingDescriptorSystem(MakoDescriptorSystem):
    """
    A system that has a cache of a course version's json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data.

    Computes the metadata inheritance upon creation.
    """
    def __init__(self, modulestore, course_entry, module_data, lazy,
        default_class, error_tracker, render_template):
        """
        Computes the metadata inheritance and sets up the cache.

        modulestore: the module store that can be used to retrieve additional
        modules

        module_data: a dict mapping Location -> json that was cached from the
            underlying modulestore

        default_class: The default_class to use when loading an
            XModuleDescriptor from the module_data

        resources_fs: a filesystem, as per MakoDescriptorSystem

        error_tracker: a function that logs errors for later display to users

        render_template: a function for rendering templates, as per
            MakoDescriptorSystem
        """
        # TODO find all references to resources_fs and make handle None
        super(CachingDescriptorSystem, self).__init__(
                self._load_item, None, error_tracker, render_template)
        self.modulestore = modulestore
        self.course_entry = course_entry
        self.lazy = lazy
        self.module_data = module_data
        self.default_class = default_class
        # TODO see if self.course_id is needed
        # Compute inheritance
        modulestore.inherit_metadata(course_entry.get('blocks', {}),
            course_entry.get('blocks', {})
            .get(course_entry.get('root')))


    def _load_item(self, usage_id):
        # TODO ensure all callers of system.load_item pass just the id
        json_data = self.module_data.get(usage_id)
        if json_data is None:
            # deeper than initial descendant fetch or doesn't exist
            self.modulestore.cache_items(self, [usage_id], lazy=self.lazy)
            json_data = self.module_data.get(usage_id)
            if json_data is None:
                raise ItemNotFoundError

        class_ = XModuleDescriptor.load_class(
            json_data.get('category'),
            self.default_class
        )
        return self.xblock_from_json(class_, usage_id, json_data)

    def xblock_from_json(self, class_, usage_id, json_data):
        try:
            # most likely a lazy loader but not the id directly
            definition = json_data.get('definition', {})
            metadata = json_data.get('metadata', {})

            kvs = SplitMongoKVS(definition,
                json_data.get('children', []),
                metadata, json_data.get('_inherited_metadata'))

            block_locator = BlockUsageLocator(version_guid=self.course_entry['_id'],
                usage_id=usage_id, course_id=self.course_entry.get('course_id'))
            model_data = DbModel(kvs, class_, None,
                SplitMongoKVSid(
                    # DbModel req's that these support .url()
                    block_locator,
                    self.modulestore.definition_locator(definition)))
            module = class_(self, json_data.get('category'),
                block_locator, self.modulestore.definition_locator(definition),
                model_data)
            return module
        except:
            log.warning("Failed to load descriptor", exc_info=True)
            return ErrorDescriptor.from_json(
                json_data,
                self,
                BlockUsageLocator(version_guid=self.course_entry['_id'],
                    usage_id=usage_id),
                error_msg=exc_info_to_str(sys.exc_info())
            )


class SplitMongoModuleStore(ModuleStoreBase):
    """
    A Mongodb backed ModuleStore supporting versions, inheritance,
    and sharing.
    """
    # temporarily caches course_id on structure if structure loaded by course_id
    # so subsequent accesses can use course_id
    VERSION_FIELDS = ('edited_on', 'edited_by', 'previous_version',
        'original_version')

    def __init__(self, host, db, collection, fs_root, render_template,
                 port=27017, default_class=None,
                 error_tracker=null_error_tracker,
                 user=None, password=None,
                 draft_aware=False,
                 **kwargs):

        ModuleStoreBase.__init__(self)

        self.db = pymongo.database.Database(pymongo.MongoClient(
            host=host,
            port=port,
            **kwargs
        ), db)

        # TODO add caching of structures to thread_cache to prevent repeated fetches (but not index b/c
        # it changes w/o having a change in id)
        self.course_index = self.db[collection + '.active_versions']
        self.structures = self.db[collection + '.structures']
        self.definitions = self.db[collection + '.definitions']
        self.draft_aware = draft_aware

        # ??? Code review question: those familiar w/ python threading. Should I instead
        # use django cache? How should I expire entries?
        # _add_cache could use a lru mechanism to control the cache size?
        self.thread_cache = threading.local()

        if user is not None and password is not None:
            self.db.authenticate(user, password)

        if draft_aware:
            # Force mongo to report errors, at the expense of performance
            # pymongo docs suck but explanation:
            # http://api.mongodb.org/java/2.10.1/com/mongodb/WriteConcern.html
            self.course_index.write_concern = {'w': 1}
            self.structures.write_concern = {'w': 1}
            self.definitions.write_concern = {'w': 1}

        if default_class is not None:
            module_path, _, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_
        else:
            self.default_class = None
        self.fs_root = path(fs_root)
        self.error_tracker = error_tracker
        self.render_template = render_template

    def cache_items(self, system, base_usage_ids, depth=0, lazy=True):
        '''
        Handles caching of items once inheritance and any other one time
        per course per fetch operations are done.
        :param system: a CachingDescriptorSystem
        :param base_usage_ids: list of usage_ids to fetch
        :param depth: how deep below these to prefetch
        :param lazy: whether to fetch definitions or use placeholders
        '''
        new_module_data = {}
        for usage_id in base_usage_ids:
            new_module_data = self.descendants(system.course_entry['blocks'],
                usage_id, depth, new_module_data)

        # remove any which were already in module_data (not sure if there's a better way)
        for newkey in new_module_data.iterkeys():
            if newkey in system.module_data:
                del new_module_data[newkey]

        if lazy:
            for block in new_module_data.itervalues():
                block['definition'] = DefinitionLazyLoader(self,
                    block['definition'])
        else:
            # Load all descendants by id
            descendent_definitions = self.definitions.find({
                '_id': {'$in': [block['definition']
                    for block in new_module_data.itervalues()]}})
            # turn into a map
            definitions = {definition['_id']: definition
                for definition in descendent_definitions}

            for block in new_module_data.itervalues():
                if block['definition'] in definitions:
                    block['definition'] = definitions[block['definition']]

        system.module_data.update(new_module_data)
        return system.module_data

    def _load_items(self, course_entry, usage_ids, depth=0, lazy=True):
        '''
        Load & cache the given blocks from the course. Prefetch down to the
        given depth. Load the definitions into each block if lazy is False;
        otherwise, use the lazy definition placeholder.
        '''
        system = self._get_cache(course_entry['_id'])
        if system is None:
            system = CachingDescriptorSystem(
                self,
                course_entry,
                {},
                lazy,
                self.default_class,
                self.error_tracker,
                self.render_template
            )
            self._add_cache(course_entry['_id'], system)
            self.cache_items(system, usage_ids, depth, lazy)
        elif 'course_id' in course_entry:
            # HACK :-( if same version ref'd by more than one course in same thread, the
            # caching of the course_id on the entry may be wrong. Force it here.
            system.course_entry['course_id'] = course_entry['course_id']
        return [system.load_item(usage_id) for usage_id in usage_ids]

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

    def _clear_cache(self):
        """
        Should only be used by testing or something which implements transactional boundary semantics
        """
        self.thread_cache.course_cache = {}

    def _lookup_course(self, course_locator):
        '''
        Decode the locator into the right series of db access. Does not
        return the CourseDescriptor! It returns the actual db json from
        structures.

        :param course_locator: any subclass of CourseLocator
        '''
        # NOTE: if and when this uses cache, the update if changed logic will break if the cache
        # holds the same objects as the descriptors!
        if (course_locator.version_guid is None and
            course_locator.course_id is None):
            raise InsufficientSpecificationError(course_locator)

        if course_locator.course_id is not None:
            # use the course_id
            index = self.course_index.find_one({'_id': course_locator.course_id})
            if index is None:
                raise ItemNotFoundError(course_locator)
            if self.wants_published(course_locator.revision):
                version_guid = index['publishedVersion']
                if version_guid is None:
                    raise ItemNotFoundError(course_locator)
            else:
                version_guid = index['draftVersion']
            if course_locator.version_guid is not None and version_guid != course_locator.version_guid:
                # This may be a bit too touchy but it's hard to infer intent
                raise VersionConflictError(course_locator, CourseLocator(course_locator, version_guid=version_guid))
        else:
            # TODO should this raise an exception if revision was provided?
            version_guid = course_locator.version_guid

        entry = self.structures.find_one({'_id': version_guid})
        if course_locator.course_id:
            entry['course_id'] = course_locator.course_id
        return entry

    def get_courses(self, qualifiers=None, revision=None):
        '''
        Returns a list of course descriptors matching any given qualifiers.
        Explicitly filters out the template course; so, you can't use this to
        get that one.

        qualifiers should be a dict of keywords matching the db fields or any
        legal query for mongo to use against the active_versions collection.

        Note, this is to find the current draft or published head versions not
        any other versions (which you'd do via get_course)
        '''
        # FIXME filter out the template course
        matching = self.course_index.find(qualifiers)
        get_published = self.wants_published(revision)

        # collect ids and then query for those
        course_ids = []
        id_version_map = {}
        if get_published:
            for course_entry in matching:
                if course_entry['publishedVersion'] is not None:
                    course_ids.append(course_entry['publishedVersion'])
                    id_version_map[course_entry['publishedVersion']] = course_entry['_id']
        else:
            for course_entry in matching:
                course_ids.append(course_entry['draftVersion'])
                id_version_map[course_entry['draftVersion']] = course_entry['_id']

        course_entries = self.structures.find({'_id': {'$in': course_ids}})

        # get the block for the course element (s/b the root)
        result = []
        for entry in course_entries:
            entry['course_id'] = id_version_map[entry['_id']]
            result.extend(self._load_items(entry, [entry['root']], 0,
                lazy=True))
        return result

    def get_course(self, course_locator):
        '''
        Gets the course descriptor for the course identified by the locator
        which may or may not be a blockLocator.

        raises InsufficientSpecificationError
        '''
        course_entry = self._lookup_course(course_locator)
        result = self._load_items(course_entry, [course_entry['root']], 0,
            lazy=True)
        return result[0]

    def get_course_for_item(self, location):
        '''
        Provided for backward compatibility. Is equivalent to calling get_course
        :param location:
        '''
        return self.get_course(location)

    def has_item(self, block_location):
        """
        Returns True if location exists in its course. Returns false if
        the course or the block w/in the course do not exist for the given version.
        raises InsufficientSpecificationError if the locator does not id a block
        """
        if block_location.usage_id is None:
            raise InsufficientSpecificationError(block_location)
        try:
            course_structure = self._lookup_course(block_location)
        except ItemNotFoundError:
            # this error only occurs if the course does not exist
            return False

        return course_structure['blocks'].get(block_location.usage_id) is not None

    def get_item(self, location, depth=0):
        """
        depth (int): An argument that some module stores may use to prefetch
            descendants of the queried modules for more efficient results later
            in the request. The depth is counted in the number of
            calls to get_children() to cache. None indicates to cache all
            descendants.
        raises InsufficientSpecificationError or ItemNotFoundError
        """
        location = BlockUsageLocator.ensure_fully_specified(location)
        course = self._lookup_course(location)
        items = self._load_items(course, [location.usage_id], depth, lazy=True)
        if len(items) == 0:
            raise ItemNotFoundError(location)
        return items[0]

    # TODO refactor this and get_courses to use a constructed query
    def get_items(self, locator, qualifiers):
        '''
        Get all of the modules in the given course matching the qualifiers. The
        qualifiers should only be fields in the structures collection (sorry).
        There will be a separate search method for searching through
        definitions.

        Common qualifiers are category, definition (provide definition id),
        metadata: {display_name ..}, children (return
        block if its children includes the one given value). If you want
        substring matching use {$regex: /acme.*corp/i} type syntax.

        Although these
        look like mongo queries, it is all done in memory; so, you cannot
        try arbitrary queries.

        :param locator: CourseLocator or BlockUsageLocator restricting search scope
        :param qualifiers: a dict restricting which elements should match
        '''
        # TODO extend to only search a subdag of the course?
        course = self._lookup_course(locator)
        items = []
        for usage_id, value in course['blocks'].iteritems():
            if self._block_matches(value, qualifiers):
                items.append(usage_id)

        if len(items) > 0:
            return self._load_items(course, items, 0, lazy=True)
        else:
            return []

    # What's the use case for usage_id being separate?
    def get_parent_locations(self, locator, usage_id=None):
        '''
        Return the locations (Locators w/ usage_ids) for the parents of this location in this
        course. Could use get_items(location, {'children': usage_id}) but this is slightly faster.
        NOTE: does not actually ensure usage_id exists
        If usage_id is None, then the locator must specify the usage_id
        '''
        if usage_id is None:
            usage_id = locator.usage_id
        course = self._lookup_course(locator)
        items = []
        for parent_id, value in course['blocks'].iteritems():
            for child_id in value['children']:
                if usage_id == child_id:
                    items.append(BlockUsageLocator(locator, usage_id=parent_id))
        return items

    def get_course_index_info(self, course_locator):
        """
        The index records the initial creation of the indexed course and tracks the current draft
        and published heads. This function is primarily for test verification but may serve some
        more general purpose.
        :param course_locator: must have a course_id set
        :return {'org': , 'prettyid': ,
            'draftVersion': the head draft version id,
            'publishedVersion': the head published version id if any,
            'edited_by': who created the course originally (named edited for consistency),
            'edited_on': when the course was originally created
        }
        """
        if course_locator.course_id is None:
            return None
        index = self.course_index.find_one({'_id': course_locator.course_id})
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
        course = self._lookup_course(course_locator)
        return {'original_version': course['original_version'],
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
        definition = self.definitions.find_one({'_id': definition_locator.def_id})
        if definition is None:
            return None
        return {'original_version': definition['original_version'],
            'previous_version': definition['previous_version'],
            'edited_by': definition['edited_by'],
            'edited_on': definition['edited_on']
        }

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
            version_guid = course.version_guid
        else:
            version_guid = course_locator.version_guid

        # TODO if depth is significant, it may make sense to get all that have the same original_version
        # and reconstruct the subtree from version_guid
        next_entries = self.structures.find({'previous_version' : version_guid})
        # must only scan cursor's once
        next_versions = [struct for struct in next_entries]
        result = {version_guid: [CourseLocator(version_guid=struct['_id']) for struct in next_versions]}
        depth = 1
        while depth < version_history_depth and len(next_versions) > 0:
            depth += 1
            next_entries = self.structures.find({'previous_version':
                {'$in': [struct['_id'] for struct in next_versions]}})
            next_versions = [struct for struct in next_entries]
            for course_structure in next_versions:
                result.setdefault(course_structure['previous_version'], []).append(
                    CourseLocator(version_guid=struct['_id']))
        return VersionTree(CourseLocator(course_locator, version_guid=version_guid), result)


    def get_block_successors(self, block_locator, version_history_depth=1):
        '''
        Find the version_history_depth next versions of this block. Return as a VersionTree
        Mostly makes sense when course_locator uses a version_guid, but because it finds all relevant
        next versions, these do include those created for other courses.
        '''
        # TODO implement
        pass

    def get_definition_successors(self, definition_locator, version_history_depth=1):
        '''
        Find the version_history_depth next versions of this definition. Return as a VersionTree
        '''
        # TODO implement
        pass

    # TODO is it an error to call create, update, or delete if self.draft_aware == False?
    def create_definition_from_data(self, new_def_data, category, user_id):
        """
        Pull the definition fields out of descriptor and save to the db as a new definition
        w/o a predecessor and return the new id.

        :param user_id: request.user object
        """
        document = {"category" : category,
            "data": new_def_data,
            "edited_by": user_id,
            "edited_on": datetime.datetime.utcnow(),
            "previous_version": None,
            "original_version": None}
        new_id = self.definitions.insert(document)
        definition_locator = DescriptionLocator(new_id)
        document['original_version'] = new_id
        self.definitions.update({'_id': new_id}, {'$set': {"original_version": new_id}})
        return definition_locator

    def update_definition_from_data(self, definition_locator, new_def_data, user_id):
        """
        See if new_def_data differs from the persisted version. If so, update
        the persisted version and return the new id.

        :param user_id: request.user
        """
        def needs_saved():
            if isinstance(new_def_data, dict):
                for key, value in new_def_data.iteritems():
                    if key not in old_definition['data'] or value != old_definition['data'][key]:
                        return True
                for key, value in old_definition['data'].iteritems():
                    if key not in new_def_data:
                        return True
            else:
                return new_def_data != old_definition['data']

        # if this looks in cache rather than fresh fetches, then it will probably not detect
        # actual change b/c the descriptor and cache probably point to the same objects
        old_definition = self.definitions.find_one({'_id': definition_locator.def_id})
        if old_definition is None:
            raise ItemNotFoundError(definition_locator.url())
        del old_definition['_id']

        if needs_saved():
            old_definition['data'] = new_def_data
            old_definition['edited_by'] = user_id
            old_definition['edited_on'] = datetime.datetime.utcnow()
            old_definition['previous_version'] = definition_locator.def_id
            new_id = self.definitions.insert(old_definition)
            return DescriptionLocator(new_id), True
        else:
            return definition_locator, False

    def _generate_usage_id(self, course_blocks, category):
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
        while category + str(serial) in course_blocks:
            serial += 1
        return category + str(serial)

    def _generate_course_id(self, id_root):
        """
        Generate a somewhat readable course id unique w/in this db using the id_root
        :param course_blocks: the current list of blocks.
        :param category:
        """
        existing_uses = self.course_index.find({"_id": {"$regex": id_root}})
        if existing_uses.count() > 0:
            max_found = 0
            matcher = re.compile(id_root + r'(\d*)')
            for entry in existing_uses:
                serial = re.search(matcher, entry['_id'])
                if serial.groups > 0:
                    value = int(serial.group(1))
                    if value > max_found:
                        max_found = value
            return id_root + str(max_found + 1)
        else:
            return id_root

    # TODO I would love to write this to take a real descriptor and persist it BUT descriptors, kvs, and dbmodel
    #      all assume locators are set and unique! Having this take the model contents piecemeal breaks the separation
    #      of model from persistence layer
    def create_item(self, course_or_parent_locator, category, user_id, definition_locator=None, new_def_data=None,
        metadata=None, force=False):
        """
        Add a descriptor to persistence as the last child of the optional parent_location or just as an element
        of the course (if no parent provided). Return the resulting post saved version with populated locators.

        If the locator is a BlockUsageLocator, then it's assumed to be the parent. If it's a CourseLocator, then it's
        merely the containing course.

        raises InsufficientSpecificationError if there is no course locator.
        raises NotDraftVersion if course_id and version_guid given and the current draft head != version_guid
            and force is not True.
        force: fork the structure and don't update the course draftVersion if the above

        The incoming definition_locator should either be None to indicate this is a brand new definition or
        a pointer to the existing definition to which this block should point or from which this was derived.
        If new_def_data is None, then definition_locator must have a value meaning that this block points
        to the existing definition. If new_def_data is not None and definition_location is not None, then
        new_def_data is assumed to be a new payload for definition_location.

        Creates a new draft of the course structure, creates and inserts the new block, makes the block point
        to the definition which may be new or a new version of an existing or an existing.
        Rules for course locator:

        * If the course locator specifies a course_id and either it doesn't
          specify version_guid or the one it specifies == the current draft, it progresses the course to point
          to the new draft and sets the active version to point to the new draft
        * If the locator has a course_id but its version_guid != current draft, the course index will not point
          to this new version although the new version will be created.
        * Note, if the version_guid == the published one, this is innocuous but mostly ineffective in that it
          will create a new version of the course to which no entries in the course index point.
        * If the course locator is just a version_guid, it's the same as the version_guid != current draft.
        NOTE: using a version_guid will end up creating a new version of the course. Your new item won't be in
        the course id'd by version_guid but instead in one w/ a new version_guid. Ensure in this case that you get
        the new version_guid from the locator in the returned object!
        """
        # find course_index entry if applicable and structures entry
        index_entry = self._get_index_if_valid(course_or_parent_locator, force)
        structure = self._lookup_course(course_or_parent_locator)

        # persist the definition if persisted != passed
        if (definition_locator is None or definition_locator.def_id is None):
            definition_locator = self.create_definition_from_data(new_def_data, category, user_id)
        elif new_def_data is not None:
            definition_locator, _ = self.update_definition_from_data(definition_locator, new_def_data, user_id)

        # copy the structure and modify the new one
        new_structure = self._version_structure(structure, user_id)
        # generate an id
        new_usage_id = self._generate_usage_id(new_structure['blocks'], category)
        if isinstance(course_or_parent_locator, BlockUsageLocator) and course_or_parent_locator.usage_id is not None:
            new_structure['blocks'][course_or_parent_locator.usage_id]['children'].append(new_usage_id)
        new_structure['blocks'][new_usage_id] = {
            "children": [],
            "category": category,
            "definition": definition_locator.def_id,
            "metadata": metadata if metadata else {}
            }
        new_id = self.structures.insert(new_structure)

        # update the index entry if appropriate
        if index_entry is not None and structure["_id"] == index_entry["draftVersion"]:
            index_entry["draftVersion"] = new_id
            self.course_index.update({"_id": index_entry["_id"]}, {"$set": {"draftVersion": new_id}})

        # fetch and return the new item--fetching is unnecessary but a good qc step
        return self.get_item(BlockUsageLocator(course_or_parent_locator, usage_id=new_usage_id, version_guid=new_id))

    # TODO should this get the org from the user object?
    def create_course(self, org, prettyid, user_id, id_root=None, metadata=None, course_data=None,
        draft_version=None, published_version=None, root_category='course'):
        """
        Create a new entry in the active courses index which points to an existing or new structure. Returns
        the course root of the resulting entry (the location has the course id)

        id_root: allows the caller to specify the course_id. It's a root in that, if it's already taken,
        this method will append things to the root to make it unique. (defaults to org)

        metadata: if provided, will set the metadata of the root course object in the new draft course. If both
        metadata and draft_version are provided, it will generate a successor version to the given draft_version,
        and update the metadata with any provided values (via update not setting).

        course_data: if provided, will update the data of the new course xblock definition to this. Like metadata,
        if provided, this will cause a new version of any given draft_version as well as a new version of the
        definition (which will point to the existing one if given a draft_version). If not provided and given
        a draft_version, it will reuse the same definition as the draft course (obvious since it's reusing the draft
        course). If not provided and no draft is given, it will be empty and get the field defaults (hopefully) when
        loaded.

        draft_version: if provided, the new course will reuse this version (unless you also provide metadata, see
        above). if not provided, will create a mostly empty course structure with just a category course root
        xblock. The draft_version can be a CourseLocator or just the version id

        published_version: if provided, the new course will treat this as its published version otherwise it
        will have no currently published version. The published_version can be a CourseLocator or just a version
        id. Note, this method will not update the published_version with any provided metadata or course_data.
        Those will remain unpublished in the draft.
        """
        if metadata is None:
            metadata = {}
        # work from inside out: definition, structure, index entry
        if draft_version is None:
            # create new definition and structure
            definition_entry = {
                'category': root_category,
                'data': {},
                'edited_by': user_id,
                'edited_on': datetime.datetime.utcnow(),
                'previous_version': None,
                }
            definition_id = self.definitions.insert(definition_entry)
            definition_entry['original_version'] = definition_id
            self.definitions.update({'_id': definition_id}, {'$set': {"original_version": definition_id}})

            draft_structure = {
                'root': 'course',
                'previous_version': None,
                'edited_by': user_id,
                'edited_on': datetime.datetime.utcnow(),
                'blocks': {
                    'course': {
                        'children':[],
                        'category': 'course',
                        'definition': definition_id,
                        'metadata': metadata}}}
            new_id = self.structures.insert(draft_structure)
            draft_structure['original_version'] = new_id
            self.structures.update({'_id': new_id}, {'$set': {"original_version": new_id}})

        else:
            # just get the draft_version structure
            if not isinstance(draft_version, CourseLocator):
                draft_version = CourseLocator(version_guid=draft_version)
            draft_structure = self._lookup_course(draft_version)
            if course_data is not None or metadata:
                draft_structure = self._version_structure(draft_structure, user_id)
                root_block = draft_structure['blocks'][draft_structure['root']]
                if metadata is not None:
                    root_block['metadata'].update(metadata)
                if course_data is not None:
                    definition = self.definitions.find_one({
                        '_id': root_block['definition']})
                    definition['data'].update(course_data)
                    definition['previous_version'] = definition['_id']
                    definition['edited_by'] = user_id
                    definition['edited_on'] = datetime.datetime.utcnow()
                    del definition['_id']
                    root_block['definition'] = self.definitions.insert(definition)
                # insert updates the '_id' in draft_structure
                new_id = self.structures.insert(draft_structure)

        # create the index entry
        if id_root is None:
            id_root = org
        new_id = self._generate_course_id(id_root)
        if isinstance(published_version, CourseLocator):
            # convert to simple version guid
            if published_version.version_guid is None:
                # need to look up course to get published version
                published_index = self.course_index.find_one({'_id': published_version.course_id})
                if published_version.revision == 'draft':
                    published_version = published_index['draftVersion']
                else:
                    published_version = published_index['publishedVersion']
            else:
                published_version = published_version.version_guid

        index_entry = {
            '_id': new_id,
            'org': org,
            'prettyid': prettyid,
            'edited_by': user_id,
            'edited_on': datetime.datetime.utcnow(),
            'draftVersion': draft_structure['_id'],
            'publishedVersion': published_version}
        new_id = self.course_index.insert(index_entry)
        return self.get_course(CourseLocator(course_id=new_id))

    # TODO refactor or remove callers
    def clone_item(self, source_course_id, dest_course_id, source, location):
        """
        Clone a new item that is a copy of the item at the location `source`
        and writes it to `location`
        """
        raise NotImplementedError("Replace w/ create or update_item")

    def update_item(self, descriptor, user_id, force=False):
        """
        Save the descriptor's definition, metadata, & children references (i.e., it doesn't descend the tree).
        Return the new descriptor (updated location).

        raises ItemNotFoundError if the location does not exist.

        Creates a new course version. If the descriptor's location has a course_id, it moves the course head
        pointer. If the version_guid of the descriptor points to a non-head version and there's been an intervening
        change to this item, it raises a VersionConflictError unless force is True. In the force case, it forks
        the course but leaves the head pointer where it is (this change will not be in the course head).

        The implementation tries to detect which, if any changes, actually need to be saved and thus won't version
        the definition, structure, nor course if they didn't change.
        """
        # TODO question: by passing a descriptor, because descriptors are only instantiable from get_item
        # and ilk, we're necessitating a read, modify, call this, which reads, modifies, and persists. Is that ok?
        original_structure = self._lookup_course(descriptor.location)
        index_entry = self._get_index_if_valid(descriptor.location, force)

        descriptor.definition_locator, is_updated = self.update_definition_from_data(
            descriptor.definition_locator, descriptor.xblock_kvs().get_data(), user_id)
        # check children
        original_entry = original_structure['blocks'][descriptor.location.usage_id]
        if (not is_updated and descriptor.has_children
            and not self._lists_equal(original_entry['children'], descriptor.children)):
            is_updated = True
        # check metadata
        if not is_updated:
            original_metadata = original_entry['metadata']
            original_keys = original_metadata.keys()
            new_metadata = descriptor.xblock_kvs().get_own_metadata()
            if len(new_metadata) != len(original_keys):
                is_updated = True
            else:
                new_keys = new_metadata.keys()
                for key in original_keys:
                    if key not in new_keys or original_metadata[key] != new_metadata[key]:
                        is_updated = True
                        break
        # if updated, rev the structure
        if is_updated:
            new_structure = self._version_structure(original_structure, user_id)
            block_data = new_structure['blocks'][descriptor.location.usage_id]
            if descriptor.has_children:
                block_data["children"] = descriptor.children

            block_data["definition"] = descriptor.definition_locator.def_id
            block_data["metadata"] = descriptor.xblock_kvs().get_own_metadata()
            new_id = self.structures.insert(new_structure)

            # update the index entry if appropriate
            if index_entry is not None and original_structure["_id"] == index_entry["draftVersion"]:
                index_entry["draftVersion"] = new_id
                self.course_index.update({"_id": index_entry["_id"]}, {"$set": {"draftVersion": new_id}})

            # fetch and return the new item--fetching is unnecessary but a good qc step
            return self.get_item(BlockUsageLocator(descriptor.location, version_guid=new_id))
        else:
            # nothing changed, just return the one sent in
            return descriptor

    # TODO change all callers to update_item
    def update_children(self, course_id, location, children):
        raise NotImplementedError()

    # TODO change all callers to update_item
    def update_metadata(self, course_id, location, metadata):
        raise NotImplementedError()

    def update_course_index(self, course_locator, new_values_dict, update_versions=False):
        """
        Change the given course's index entry for the given fields. new_values_dict
        should be a subset of the dict returned by get_course_index_info.
        It cannot include '_id' (will raise IllegalArgument).
        Provide update_versions=True if you intend this to update draftVersion or publishedVersion.
        Note, this operation can be dangerous and break running courses.

        If the dict includes either value and not update_versions, it will raise an exception.

        If the dict includes edited_on or edited_by, it will raise an exception

        Does not return anything useful.
        """
        # TODO how should this log the change? edited_on and edited_by for this entry
        # has the semantic of who created the course and when; so, changing those will lose
        # that information.
        if '_id' in new_values_dict:
            raise ValueError("Cannot override _id")
        if 'edited_on' in new_values_dict or 'edited_by' in new_values_dict:
            raise ValueError("Cannot set edited_on or edited_by")
        if not update_versions and 'draftVersion' in new_values_dict:
            raise ValueError("Cannot override draftVersion without setting update_versions")
        if not update_versions and 'publishedVersion' in new_values_dict:
            raise ValueError("Cannot override publishedVersion without setting update_versions")
        self.course_index.update({'_id': course_locator.course_id},
            {'$set': new_values_dict})

    def delete_item(self, usage_locator, user_id, force=False):
        """
        Delete the tree rooted at block and any references w/in the course to the block
        from a new version of the course structure.

        returns CourseLocator for new version

        raises ItemNotFoundError if the location does not exist.
        raises ValueError if usage_locator points to the structure root

        Creates a new course version. If the descriptor's location has a course_id, it moves the course head
        pointer. If the version_guid of the descriptor points to a non-head version and there's been an intervening
        change to this item, it raises a VersionConflictError unless force is True. In the force case, it forks
        the course but leaves the head pointer where it is (this change will not be in the course head).
        """
        BlockUsageLocator.ensure_fully_specified(usage_locator)
        original_structure = self._lookup_course(usage_locator)
        if original_structure['root'] == usage_locator.usage_id:
            raise ValueError("Cannot delete the root of a course")
        index_entry = self._get_index_if_valid(usage_locator, force)
        new_structure = self._version_structure(original_structure, user_id)
        new_blocks = new_structure['blocks']
        parents = self.get_parent_locations(usage_locator)
        for parent in parents:
            new_blocks[parent.usage_id]['children'].remove(usage_locator.usage_id)
        # remove subtree
        def remove_subtree(usage_id):
            for child in new_blocks[usage_id]['children']:
                remove_subtree(child)
            del new_blocks[usage_id]
        remove_subtree(usage_locator.usage_id)

        # update index if appropriate and structures
        new_id = self.structures.insert(new_structure)
        result = CourseLocator(version_guid=new_id)

        # update the index entry if appropriate
        if index_entry is not None and original_structure["_id"] == index_entry["draftVersion"]:
            index_entry["draftVersion"] = new_id
            self.course_index.update({"_id": index_entry["_id"]}, {"$set": {"draftVersion": new_id}})
            result.course_id = usage_locator.course_id
            result.revision = usage_locator.revision

        return result

    # TODO remove all callers and then this
    def get_errored_courses(self):
        """
        This function doesn't make sense for the mongo modulestore, as structures
        are loaded on demand, rather than up front
        """
        return {}

    def inherit_metadata(self, block_map, block, inheriting_metadata=None):
        """
        Updates block with any value
        that exist in inheriting_metadata and don't appear in block['metadata'],
        and then inherits block['metadata'] to all of the children in
        block['children']. Filters by inheritance.INHERITABLE_METADATA
        """
        if block is None:
            return

        if inheriting_metadata is None:
            inheriting_metadata = {}

        # the currently passed down values take precedence over any previously cached ones
        # NOTE: this should show the values which all fields would have if inherited: i.e.,
        # not set to the locally defined value but to value set by nearest ancestor who sets it
        block.setdefault('_inherited_metadata', {}).update(inheriting_metadata)

        # update the inheriting w/ what should pass to children
        inheriting_metadata = block['_inherited_metadata'].copy()
        for field in inheritance.INHERITABLE_METADATA:
            if field in block['metadata']:
                inheriting_metadata[field] = block['metadata'][field]

        for child in block.get('children', []):
            self.inherit_metadata(block_map, block_map[child], inheriting_metadata)

    def descendants(self, block_map, usage_id, depth, descendent_map):
        """
        adds block and its descendants out to depth to descendent_map
        Depth specifies the number of levels of descendants to return
        (0 => this usage only, 1 => this usage and its children, etc...)
        A depth of None returns all descendants
        """
        if usage_id not in block_map:
            return descendent_map

        # do I need to copy the entry or is the independence of the
        # find results sufficient?
        if usage_id not in descendent_map:
            descendent_map[usage_id] = block_map[usage_id]

        if depth is None or depth > 0:
            depth = depth - 1 if depth is not None else None
            for child in block_map[usage_id].get('children', []):
                descendent_map = self.descendants(block_map, child, depth,
                    descendent_map)

        return descendent_map

    def wants_published(self, revision):
        if revision == 'draft':
            return False
        if revision == 'published':
            return True
        else:
            return not self.draft_aware

    def definition_locator(self, definition):
        '''
        Pull the id out of the definition w/ correct semantics for its
        representation
        '''
        if isinstance(definition, DefinitionLazyLoader):
            return definition.definition_locator
        else:
            return DescriptionLocator(definition['_id'])

    def _block_matches(self, value, qualifiers):
        '''
        Return True or False depending on whether the value (block contents)
        matches the qualifiers as per get_items
        :param value:
        :param qualifiers:
        '''
        for key, criteria in qualifiers.iteritems():
            if key in value:
                target = value[key]
                if not self._value_matches(target, criteria):
                    return False
            elif criteria is not None:
                return False
        return True

    def _value_matches(self, target, criteria):
        ''' helper for _block_matches '''
        if isinstance(target, list):
            return any(self._value_matches(ele, criteria)
                for ele in target)
        elif isinstance(criteria, dict):
            if '$regex' in criteria:
                return re.search(criteria['$regex'], target) is not None
            elif not isinstance(target, dict):
                return False
            else:
                return (isinstance(target, dict) and
                        self._block_matches(target, criteria))
        else:
            return criteria == target

    def _lists_equal(self, lista, listb):
        """
        The obvious function but local b/c I don't want some arcane method in the persistence layer
        becoming the universal util
        :param lista:
        :param listb:
        """
        if len(lista) != len(listb):
            return False
        for idx in enumerate(lista):
            if lista[idx] != listb[idx]:
                return False
        return True

    def _get_index_if_valid(self, locator, force=False):
        """
        If the locator identifies a course and points to its draft (or plausibly its draft),
        then return the index entry.

        raises NotDraftVersion if not the right version

        :param locator:
        """
        if locator.course_id is None:
            return None
        else:
            index_entry = self.course_index.find_one({'_id': locator.course_id})
            if (locator.version_guid is not None
                and index_entry['draftVersion'] != locator.version_guid
                and not force):
                raise NotDraftVersion(locator,
                    CourseLocator(course_id=index_entry['_id'], version_guid=index_entry['draftVersion']))
            else:
                return index_entry

    def _version_structure(self, structure, user_id):
        """
        Copy the structure and update the history info (edited_by, edited_on, previous_version)
        :param structure:
        :param user_id:
        """
        new_structure = structure.copy()
        new_structure['blocks'] = new_structure['blocks'].copy()
        del new_structure['_id']
        new_structure['previous_version'] = structure['_id']
        new_structure['edited_by'] = user_id
        new_structure['edited_on'] = datetime.datetime.utcnow()
        return new_structure
