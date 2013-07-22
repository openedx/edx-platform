"""
Modulestore backed by Mongodb.

Stores individual XModules as single documents with the following
structure:

{
    '_id': <location.as_dict>,
    'metadata': <dict containing all Scope.settings fields>
    'definition': <dict containing all Scope.content fields>
    'definition.children': <list of all child location.url()s>
}
"""

import pymongo
import sys
import logging
import copy

from collections import namedtuple
from fs.osfs import OSFS
from itertools import repeat
from path import path
from operator import attrgetter
from uuid import uuid4

from importlib import import_module
from xmodule.errortracker import null_error_tracker, exc_info_to_str
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.x_module import XModuleDescriptor
from xmodule.error_module import ErrorDescriptor
from xblock.runtime import DbModel, KeyValueStore, InvalidScopeError
from xblock.core import Scope

from xmodule.modulestore import ModuleStoreBase, Location, namedtuple_to_son
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.inheritance import own_metadata, INHERITABLE_METADATA, inherit_metadata

log = logging.getLogger(__name__)

# TODO (cpennington): This code currently operates under the assumption that
# there is only one revision for each item. Once we start versioning inside the CMS,
# that assumption will have to change


def get_course_id_no_run(location):
    '''
    Return the first two components of the course_id for this location (org/course)
    '''
    return "/".join([location.org, location.course])


class InvalidWriteError(Exception):
    """
    Raised to indicate that writing to a particular key
    in the KeyValueStore is disabled
    """


class MongoKeyValueStore(KeyValueStore):
    """
    A KeyValueStore that maps keyed data access to one of the 3 data areas
    known to the MongoModuleStore (data, children, and metadata)
    """
    def __init__(self, data, children, metadata, location, category):
        self._data = data
        self._children = children
        self._metadata = metadata
        self._location = location
        self._category = category

    def get(self, key):
        if key.scope == Scope.children:
            return self._children
        elif key.scope == Scope.parent:
            return None
        elif key.scope == Scope.settings:
            return self._metadata[key.field_name]
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                return self._location
            elif key.field_name == 'category':
                return self._category
            elif key.field_name == 'data' and not isinstance(self._data, dict):
                return self._data
            else:
                return self._data[key.field_name]
        else:
            raise InvalidScopeError(key.scope)

    def set(self, key, value):
        if key.scope == Scope.children:
            self._children = value
        elif key.scope == Scope.settings:
            self._metadata[key.field_name] = value
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                self._location = value
            elif key.field_name == 'category':
                self._category = value
            elif key.field_name == 'data' and not isinstance(self._data, dict):
                self._data = value
            else:
                self._data[key.field_name] = value
        else:
            raise InvalidScopeError(key.scope)

    def delete(self, key):
        if key.scope == Scope.children:
            self._children = []
        elif key.scope == Scope.settings:
            if key.field_name in self._metadata:
                del self._metadata[key.field_name]
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                self._location = Location(None)
            elif key.field_name == 'category':
                self._category = None
            elif key.field_name == 'data' and not isinstance(self._data, dict):
                self._data = None
            else:
                del self._data[key.field_name]
        else:
            raise InvalidScopeError(key.scope)

    def has(self, key):
        if key.scope in (Scope.children, Scope.parent):
            return True
        elif key.scope == Scope.settings:
            return key.field_name in self._metadata
        elif key.scope == Scope.content:
            if key.field_name == 'location':
                # WHY TRUE? if it's been deleted should it be False?
                return True
            elif key.field_name == 'category':
                return self._category is not None
            elif key.field_name == 'data' and not isinstance(self._data, dict):
                return True
            else:
                return key.field_name in self._data
        else:
            return False


MongoUsage = namedtuple('MongoUsage', 'id, def_id')


class CachingDescriptorSystem(MakoDescriptorSystem):
    """
    A system that has a cache of module json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data
    TODO (cdodge) when the 'split module store' work has been completed we can remove all
    references to metadata_inheritance_tree
    """
    def __init__(self, modulestore, module_data, default_class, resources_fs,
                 error_tracker, render_template, cached_metadata=None):
        """
        modulestore: the module store that can be used to retrieve additional modules

        module_data: a dict mapping Location -> json that was cached from the
            underlying modulestore

        default_class: The default_class to use when loading an
            XModuleDescriptor from the module_data

        resources_fs: a filesystem, as per MakoDescriptorSystem

        error_tracker: a function that logs errors for later display to users

        render_template: a function for rendering templates, as per
            MakoDescriptorSystem
        """
        super(CachingDescriptorSystem, self).__init__(self.load_item, resources_fs,
                                                      error_tracker, render_template)
        self.modulestore = modulestore
        self.module_data = module_data
        self.default_class = default_class
        # cdodge: other Systems have a course_id attribute defined. To keep things consistent, let's
        # define an attribute here as well, even though it's None
        self.course_id = None
        self.cached_metadata = cached_metadata

    def load_item(self, location):
        """
        Return an XModule instance for the specified location
        """
        location = Location(location)
        json_data = self.module_data.get(location)
        if json_data is None:
            module = self.modulestore.get_item(location)
            if module is not None:
                # update our own cache after going to the DB to get cache miss
                self.module_data.update(module.system.module_data)
            return module
        else:
            # load the module and apply the inherited metadata
            try:
                category = json_data['location']['category']
                class_ = XModuleDescriptor.load_class(
                    category,
                    self.default_class
                )
                definition = json_data.get('definition', {})
                metadata = json_data.get('metadata', {})
                for old_name, new_name in class_.metadata_translations.items():
                    if old_name in metadata:
                        metadata[new_name] = metadata[old_name]
                        del metadata[old_name]

                kvs = MongoKeyValueStore(
                    definition.get('data', {}),
                    definition.get('children', []),
                    metadata,
                    location,
                    category
                )

                model_data = DbModel(kvs, class_, None, MongoUsage(self.course_id, location))
                model_data['category'] = category
                model_data['location'] = location
                module = class_(self, model_data)
                if self.cached_metadata is not None:
                    # parent container pointers don't differentiate between draft and non-draft
                    # so when we do the lookup, we should do so with a non-draft location
                    non_draft_loc = location.replace(revision=None)
                    metadata_to_inherit = self.cached_metadata.get(non_draft_loc.url(), {})
                    inherit_metadata(module, metadata_to_inherit)
                return module
            except:
                log.warning("Failed to load descriptor", exc_info=True)
                return ErrorDescriptor.from_json(
                    json_data,
                    self,
                    json_data['location'],
                    error_msg=exc_info_to_str(sys.exc_info())
                )


def location_to_query(location, wildcard=True):
    """
    Takes a Location and returns a SON object that will query for that location.
    Fields in location that are None are ignored in the query

    If `wildcard` is True, then a None in a location is treated as a wildcard
    query. Otherwise, it is searched for literally
    """
    query = namedtuple_to_son(Location(location), prefix='_id.')

    if wildcard:
        for key, value in query.items():
            # don't allow wildcards on revision, since public is set as None, so
            # its ambiguous between None as a real value versus None=wildcard
            if value is None and key != '_id.revision':
                del query[key]

    return query


metadata_cache_key = attrgetter('org', 'course')


class MongoModuleStore(ModuleStoreBase):
    """
    A Mongodb backed ModuleStore
    """

    # TODO (cpennington): Enable non-filesystem filestores
    def __init__(self, host, db, collection, fs_root, render_template,
                 port=27017, default_class=None,
                 error_tracker=null_error_tracker,
                 user=None, password=None, request_cache=None,
                 metadata_inheritance_cache_subsystem=None, **kwargs):

        super(MongoModuleStore, self).__init__()

        self.collection = pymongo.connection.Connection(
            host=host,
            port=port,
            tz_aware=True,
            **kwargs
        )[db][collection]

        if user is not None and password is not None:
            self.collection.database.authenticate(user, password)

        # Force mongo to report errors, at the expense of performance
        self.collection.safe = True

        # Force mongo to maintain an index over _id.* that is in the same order
        # that is used when querying by a location
        self.collection.ensure_index(
            zip(('_id.' + field for field in Location._fields), repeat(1)))

        if default_class is not None:
            module_path, _, class_name = default_class.rpartition('.')
            class_ = getattr(import_module(module_path), class_name)
            self.default_class = class_
        else:
            self.default_class = None
        self.fs_root = path(fs_root)
        self.error_tracker = error_tracker
        self.render_template = render_template
        self.ignore_write_events_on_courses = []
        self.request_cache = request_cache
        self.metadata_inheritance_cache_subsystem = metadata_inheritance_cache_subsystem

    def compute_metadata_inheritance_tree(self, location):
        '''
        TODO (cdodge) This method can be deleted when the 'split module store' work has been completed
        '''

        # get all collections in the course, this query should not return any leaf nodes
        # note this is a bit ugly as when we add new categories of containers, we have to add it here
        query = {'_id.org': location.org,
                 '_id.course': location.course,
                 '_id.category': {'$in': ['course', 'chapter', 'sequential', 'vertical',
                                          'wrapper', 'problemset', 'conditional', 'randomize']}
                 }
        # we just want the Location, children, and inheritable metadata
        record_filter = {'_id': 1, 'definition.children': 1}

        # just get the inheritable metadata since that is all we need for the computation
        # this minimizes both data pushed over the wire
        for attr in INHERITABLE_METADATA:
            record_filter['metadata.{0}'.format(attr)] = 1

        # call out to the DB
        resultset = self.collection.find(query, record_filter)

        results_by_url = {}
        root = None

        # now go through the results and order them by the location url
        for result in resultset:
            location = Location(result['_id'])
            # We need to collate between draft and non-draft
            # i.e. draft verticals can have children which are not in non-draft versions
            location = location.replace(revision=None)
            location_url = location.url()
            if location_url in results_by_url:
                existing_children = results_by_url[location_url].get('definition', {}).get('children', [])
                additional_children = result.get('definition', {}).get('children', [])
                total_children = existing_children + additional_children
                if 'definition' not in results_by_url[location_url]:
                    results_by_url[location_url]['definition'] = {}
                results_by_url[location_url]['definition']['children'] = total_children
            results_by_url[location.url()] = result
            if location.category == 'course':
                root = location.url()

        # now traverse the tree and compute down the inherited metadata
        metadata_to_inherit = {}

        def _compute_inherited_metadata(url):
            """
            Helper method for computing inherited metadata for a specific location url
            """
            # check for presence of metadata key. Note that a given module may not yet be fully formed.
            # example: update_item -> update_children -> update_metadata sequence on new item create
            # if we get called here without update_metadata called first then 'metadata' hasn't been set
            # as we're not fully transactional at the DB layer. Same comment applies to below key name
            # check
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

    def get_cached_metadata_inheritance_tree(self, location, force_refresh=False):
        '''
        TODO (cdodge) This method can be deleted when the 'split module store' work has been completed
        '''
        key = metadata_cache_key(location)
        tree = {}

        if not force_refresh:
            # see if we are first in the request cache (if present)
            if self.request_cache is not None and key in self.request_cache.data.get('metadata_inheritance', {}):
                return self.request_cache.data['metadata_inheritance'][key]

            # then look in any caching subsystem (e.g. memcached)
            if self.metadata_inheritance_cache_subsystem is not None:
                tree = self.metadata_inheritance_cache_subsystem.get(key, {})
            else:
                logging.warning('Running MongoModuleStore without a metadata_inheritance_cache_subsystem. This is OK in localdev and testing environment. Not OK in production.')

        if not tree:
            # if not in subsystem, or we are on force refresh, then we have to compute
            tree = self.compute_metadata_inheritance_tree(location)

            # now write out computed tree to caching subsystem (e.g. memcached), if available
            if self.metadata_inheritance_cache_subsystem is not None:
                self.metadata_inheritance_cache_subsystem.set(key, tree)

        # now populate a request_cache, if available. NOTE, we are outside of the
        # scope of the above if: statement so that after a memcache hit, it'll get
        # put into the request_cache
        if self.request_cache is not None:
            # we can't assume the 'metadatat_inheritance' part of the request cache dict has been
            # defined
            if 'metadata_inheritance' not in self.request_cache.data:
                self.request_cache.data['metadata_inheritance'] = {}
            self.request_cache.data['metadata_inheritance'][key] = tree

        return tree

    def refresh_cached_metadata_inheritance_tree(self, location):
        """
        Refresh the cached metadata inheritance tree for the org/course combination
        for location
        """
        pseudo_course_id = '/'.join([location.org, location.course])
        if pseudo_course_id not in self.ignore_write_events_on_courses:
            self.get_cached_metadata_inheritance_tree(location, force_refresh=True)

    def _clean_item_data(self, item):
        """
        Renames the '_id' field in item to 'location'
        """
        item['location'] = item['_id']
        del item['_id']

    def _query_children_for_cache_children(self, items):
        # first get non-draft in a round-trip
        query = {
            '_id': {'$in': [namedtuple_to_son(Location(item)) for item in items]}
        }
        return list(self.collection.find(query))

    def _cache_children(self, items, depth=0):
        """
        Returns a dictionary mapping Location -> item data, populated with json data
        for all descendents of items up to the specified depth.
        (0 = no descendents, 1 = children, 2 = grandchildren, etc)
        If depth is None, will load all the children.
        This will make a number of queries that is linear in the depth.
        """

        data = {}
        to_process = list(items)
        while to_process and depth is None or depth >= 0:
            children = []
            for item in to_process:
                self._clean_item_data(item)
                children.extend(item.get('definition', {}).get('children', []))
                data[Location(item['location'])] = item

            if depth == 0:
                break

            # Load all children by id. See
            # http://www.mongodb.org/display/DOCS/Advanced+Queries#AdvancedQueries-%24or
            # for or-query syntax
            to_process = []
            if children:
                to_process = self._query_children_for_cache_children(children)

            # If depth is None, then we just recurse until we hit all the descendents
            if depth is not None:
                depth -= 1

        return data

    def _load_item(self, item, data_cache, apply_cached_metadata=True):
        """
        Load an XModuleDescriptor from item, using the children stored in data_cache
        """
        data_dir = getattr(item, 'data_dir', item['location']['course'])
        root = self.fs_root / data_dir

        if not root.isdir():
            root.mkdir()

        resource_fs = OSFS(root)

        cached_metadata = {}
        if apply_cached_metadata:
            cached_metadata = self.get_cached_metadata_inheritance_tree(Location(item['location']))

        # TODO (cdodge): When the 'split module store' work has been completed, we should remove
        # the 'metadata_inheritance_tree' parameter
        system = CachingDescriptorSystem(
            self,
            data_cache,
            self.default_class,
            resource_fs,
            self.error_tracker,
            self.render_template,
            cached_metadata,
        )
        return system.load_item(item['location'])

    def _load_items(self, items, depth=0):
        """
        Load a list of xmodules from the data in items, with children cached up
        to specified depth
        """
        data_cache = self._cache_children(items, depth)

        # if we are loading a course object, if we're not prefetching children (depth != 0) then don't
        # bother with the metadata inheritance
        return [self._load_item(item, data_cache,
                apply_cached_metadata=(item['location']['category'] != 'course' or depth != 0)) for item in items]

    def get_courses(self):
        '''
        Returns a list of course descriptors.
        '''
        # TODO (vshnayder): Why do I have to specify i4x here?
        course_filter = Location("i4x", category="course")
        return [
            course
            for course
            in self.get_items(course_filter)
            if not (
                course.location.org == 'edx' and
                course.location.course == 'templates'
            )
        ]

    def _find_one(self, location):
        '''Look for a given location in the collection.  If revision is not
        specified, returns the latest.  If the item is not present, raise
        ItemNotFoundError.
        '''
        item = self.collection.find_one(
            location_to_query(location, wildcard=False),
            sort=[('revision', pymongo.ASCENDING)],
        )
        if item is None:
            raise ItemNotFoundError(location)
        return item

    def has_item(self, course_id, location):
        """
        Returns True if location exists in this ModuleStore.
        """
        location = Location.ensure_fully_specified(location)
        try:
            self._find_one(location)
            return True
        except ItemNotFoundError:
            return False

    def get_item(self, location, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises
            xmodule.modulestore.exceptions.ItemNotFoundError

        location: a Location object
        depth (int): An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of
            calls to get_children() to cache. None indicates to cache all descendents.
        """
        location = Location.ensure_fully_specified(location)
        item = self._find_one(location)
        module = self._load_items([item], depth)[0]
        return module

    def get_instance(self, course_id, location, depth=0):
        """
        TODO (vshnayder): implement policy tracking in mongo.
        For now, just delegate to get_item and ignore policy.

        depth (int): An argument that some module stores may use to prefetch
            descendents of the queried modules for more efficient results later
            in the request. The depth is counted in the number of
            calls to get_children() to cache. None indicates to cache all descendents.
        """
        return self.get_item(location, depth=depth)

    def get_items(self, location, course_id=None, depth=0):
        items = self.collection.find(
            location_to_query(location),
            sort=[('revision', pymongo.ASCENDING)],
        )

        modules = self._load_items(list(items), depth)
        return modules

    def create_xmodule(self, location, definition_data=None, metadata=None, system=None):
        """
        Create the new xmodule but don't save it. Returns the new module.

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param system: if you already have an xmodule from the course, the xmodule.system value
        """
        if not isinstance(location, Location):
            location = Location(location)
        # differs from split mongo in that I believe most of this logic should be above the persistence
        # layer but added it here to enable quick conversion. I'll need to reconcile these.
        if metadata is None:
            metadata = {}
        if system is None:
            system = CachingDescriptorSystem(
                self,
                {},
                self.default_class,
                None,
                self.error_tracker,
                self.render_template,
                {}
            )
        xblock_class = XModuleDescriptor.load_class(location.category, self.default_class)
        if definition_data is None:
            if hasattr(xblock_class, 'data') and getattr(xblock_class, 'data').default is not None:
                definition_data = getattr(xblock_class, 'data').default
            else:
                definition_data = {}
        dbmodel = self._create_new_model_data(location.category, location, definition_data, metadata)
        xmodule = xblock_class(system, dbmodel)
        return xmodule

    def save_xmodule(self, xmodule):
        """
        Save the given xmodule (will either create or update based on whether id already exists).
        Pulls out the data definition v metadata v children locally but saves it all.

        :param xmodule:
        """
        # Save any changes to the xmodule to the MongoKeyValueStore
        xmodule.save()
        # split mongo's persist_dag is more general and useful.
        self.collection.save({
                '_id': xmodule.location.dict(),
                'metadata': own_metadata(xmodule),
                'definition': {
                    'data': xmodule.xblock_kvs._data,
                    'children': xmodule.children if xmodule.has_children else []
                }
            })
        # recompute (and update) the metadata inheritance tree which is cached
        self.refresh_cached_metadata_inheritance_tree(xmodule.location)
        self.fire_updated_modulestore_signal(get_course_id_no_run(xmodule.location), xmodule.location)

    def create_and_save_xmodule(self, location, definition_data=None, metadata=None, system=None):
        """
        Create the new xmodule and save it. Does not return the new module because if the caller
        will insert it as a child, it's inherited metadata will completely change. The difference
        between this and just doing create_xmodule and save_xmodule is this ensures static_tabs get
        pointed to by the course.

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param system: if you already have an xmodule from the course, the xmodule.system value
        """
        # differs from split mongo in that I believe most of this logic should be above the persistence
        # layer but added it here to enable quick conversion. I'll need to reconcile these.
        new_object = self.create_xmodule(location, definition_data, metadata, system)
        location = new_object.location
        self.save_xmodule(new_object)

        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        # TODO move this special casing to app tier (similar to attaching new element to parent)
        if location.category == 'static_tab':
            course = self.get_course_for_item(location)
            existing_tabs = course.tabs or []
            existing_tabs.append({
                'type': 'static_tab',
                'name': new_object.display_name,
                'url_slug': new_object.location.name
            })
            course.tabs = existing_tabs
            # Save any changes to the course to the MongoKeyValueStore
            course.save()
            self.update_metadata(course.location, course.xblock_kvs._metadata)

    def fire_updated_modulestore_signal(self, course_id, location):
        """
        Send a signal using `self.modulestore_update_signal`, if that has been set
        """
        if self.modulestore_update_signal is not None:
            self.modulestore_update_signal.send(self, modulestore=self, course_id=course_id,
                                                location=location)

    def get_course_for_item(self, location, depth=0):
        '''
        VS[compat]
        cdodge: for a given Xmodule, return the course that it belongs to
        NOTE: This makes a lot of assumptions about the format of the course location
        Also we have to assert that this module maps to only one course item - it'll throw an
        assert if not
        This is only used to support static_tabs as we need to be course module aware
        '''

        # @hack! We need to find the course location however, we don't
        # know the 'name' parameter in this context, so we have
        # to assume there's only one item in this query even though we are not specifying a name
        course_search_location = ['i4x', location.org, location.course, 'course', None]
        courses = self.get_items(course_search_location, depth=depth)

        # make sure we found exactly one match on this above course search
        found_cnt = len(courses)
        if found_cnt == 0:
            raise Exception('Could not find course at {0}'.format(course_search_location))

        if found_cnt > 1:
            raise Exception('Found more than one course at {0}. There should only be one!!! '
                            'Dump = {1}'.format(course_search_location, courses))

        return courses[0]

    def _update_single_item(self, location, update):
        """
        Set update on the specified item, and raises ItemNotFoundError
        if the location doesn't exist
        """

        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        result = self.collection.update(
            {'_id': Location(location).dict()},
            {'$set': update},
            multi=False,
            upsert=True,
            # Must include this to avoid the django debug toolbar (which defines the deprecated "safe=False")
            # from overriding our default value set in the init method.
            safe=self.collection.safe
        )
        if result['n'] == 0:
            raise ItemNotFoundError(location)

    def update_item(self, location, data, allow_not_found=False):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        try:
            self._update_single_item(location, {'definition.data': data})
        except ItemNotFoundError:
            if not allow_not_found:
                raise

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        children

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """

        self._update_single_item(location, {'definition.children': children})
        # recompute (and update) the metadata inheritance tree which is cached
        self.refresh_cached_metadata_inheritance_tree(Location(location))
        # fire signal that we've written to DB
        self.fire_updated_modulestore_signal(get_course_id_no_run(Location(location)), Location(location))

    def update_metadata(self, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """
        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        loc = Location(location)
        if loc.category == 'static_tab':
            course = self.get_course_for_item(loc)
            existing_tabs = course.tabs or []
            for tab in existing_tabs:
                if tab.get('url_slug') == loc.name:
                    tab['name'] = metadata.get('display_name')
                    break
            course.tabs = existing_tabs
            # Save the updates to the course to the MongoKeyValueStore
            course.save()
            self.update_metadata(course.location, own_metadata(course))

        self._update_single_item(location, {'metadata': metadata})
        # recompute (and update) the metadata inheritance tree which is cached
        self.refresh_cached_metadata_inheritance_tree(loc)
        self.fire_updated_modulestore_signal(get_course_id_no_run(Location(location)), Location(location))

    def delete_item(self, location, delete_all_versions=False):
        """
        Delete an item from this modulestore

        location: Something that can be passed to Location
        delete_all_versions: is here because the DraftMongoModuleStore needs it and we need to keep the interface the same. It is unused.
        """
        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if location.category == 'static_tab':
            item = self.get_item(location)
            course = self.get_course_for_item(item.location)
            existing_tabs = course.tabs or []
            course.tabs = [tab for tab in existing_tabs if tab.get('url_slug') != location.name]
            # Save the updates to the course to the MongoKeyValueStore
            course.save()
            self.update_metadata(course.location, own_metadata(course))

        # Must include this to avoid the django debug toolbar (which defines the deprecated "safe=False")
        # from overriding our default value set in the init method.
        self.collection.remove({'_id': Location(location).dict()}, safe=self.collection.safe)
        # recompute (and update) the metadata inheritance tree which is cached
        self.refresh_cached_metadata_inheritance_tree(Location(location))
        self.fire_updated_modulestore_signal(get_course_id_no_run(Location(location)), Location(location))

    def get_parent_locations(self, location, course_id):
        '''Find all locations that are the parents of this location in this
        course.  Needed for path_to_location().
        '''
        location = Location.ensure_fully_specified(location)
        items = self.collection.find({'definition.children': location.url()},
                                     {'_id': True})
        return [i['_id'] for i in items]

    def get_errored_courses(self):
        """
        This function doesn't make sense for the mongo modulestore, as courses
        are loaded on demand, rather than up front
        """
        return {}

    def _create_new_model_data(self, category, location, definition_data, metadata):
        """
        To instantiate a new xmodule which will be saved latter, set up the dbModel and kvs
        """
        kvs = MongoKeyValueStore(
            definition_data,
            [],
            metadata,
            location,
            category
        )

        class_ = XModuleDescriptor.load_class(
                    category,
                    self.default_class
                )
        model_data = DbModel(kvs, class_, None, MongoUsage(None, location))
        model_data['category'] = category
        model_data['location'] = location
        return model_data
