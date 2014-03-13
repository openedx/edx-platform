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

from bson.son import SON
from fs.osfs import OSFS
from itertools import repeat
from path import path

from importlib import import_module
from xmodule.errortracker import null_error_tracker, exc_info_to_str
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.error_module import ErrorDescriptor
from xmodule.html_module import AboutDescriptor
from xblock.runtime import KvsFieldData
from xblock.exceptions import InvalidScopeError
from xblock.fields import Scope, ScopeIds

from xmodule.modulestore import ModuleStoreWriteBase, Location, MONGO_MODULESTORE_TYPE
from xmodule.modulestore.keys import CourseKey
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.inheritance import own_metadata, InheritanceMixin, inherit_metadata, InheritanceKeyValueStore
from xblock.core import XBlock

log = logging.getLogger(__name__)


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


class CachingDescriptorSystem(MakoDescriptorSystem):
    """
    A system that has a cache of module json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data
    TODO (cdodge) when the 'split module store' work has been completed we can remove all
    references to metadata_inheritance_tree
    """
    def __init__(self, modulestore, module_data, default_class, cached_metadata, **kwargs):
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

                kvs = MongoKeyValueStore(
                    definition.get('data', {}),
                    definition.get('children', []),
                    metadata,
                )

                field_data = KvsFieldData(kvs)
                scope_ids = ScopeIds(None, category, location, location)
                module = self.construct_xblock_from_class(class_, scope_ids, field_data)
                if self.cached_metadata is not None:
                    # parent container pointers don't differentiate between draft and non-draft
                    # so when we do the lookup, we should do so with a non-draft location
                    non_draft_loc = location.replace(revision=None)

                    # Convert the serialized fields values in self.cached_metadata
                    # to python values
                    metadata_to_inherit = self.cached_metadata.get(non_draft_loc.url(), {})
                    inherit_metadata(module, metadata_to_inherit)
                # decache any computed pending field settings
                module.save()
                return module
            except:
                log.warning("Failed to load descriptor", exc_info=True)
                return ErrorDescriptor.from_json(
                    json_data,
                    self,
                    json_data['location'],
                    error_msg=exc_info_to_str(sys.exc_info())
                )


def namedtuple_to_son(namedtuple, prefix=''):
    """
    Converts a namedtuple into a SON object with the same key order
    """
    son = SON()
    # pylint: disable=protected-access
    for idx, field_name in enumerate(namedtuple._fields):
        son[prefix + field_name] = namedtuple[idx]
    return son


# TODO check whether this still has purpose
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


def metadata_cache_key(location):
    """Turn a `Location` into a useful cache key."""
    return u"{0.org}/{0.course}".format(location)


class MongoModuleStore(ModuleStoreWriteBase):
    """
    A Mongodb backed ModuleStore
    """
    reference_type = Location

    # TODO (cpennington): Enable non-filesystem filestores
    # pylint: disable=C0103
    # pylint: disable=W0201
    def __init__(self, doc_store_config, fs_root, render_template,
                 default_class=None,
                 error_tracker=null_error_tracker,
                 i18n_service=None,
                 **kwargs):
        """
        :param doc_store_config: must have a host, db, and collection entries. Other common entries: port, tz_aware.
        """

        super(MongoModuleStore, self).__init__(**kwargs)

        def do_connection(
            db, collection, host, port=27017, tz_aware=True, user=None, password=None, **kwargs
        ):
            """
            Create & open the connection, authenticate, and provide pointers to the collection
            """
            self.database = pymongo.database.Database(
                pymongo.MongoClient(
                    host=host,
                    port=port,
                    tz_aware=tz_aware,
                    **kwargs
                ),
                db
            )
            self.collection = self.database[collection]

            if user is not None and password is not None:
                self.database.authenticate(user, password)

        do_connection(**doc_store_config)

        # Force mongo to report errors, at the expense of performance
        self.collection.write_concern = {'w': 1}

        # Force mongo to maintain an index over _id.* that is in the same order
        # that is used when querying by a location
        # pylint: disable=no-member, protected_access
        self.collection.ensure_index(
            zip(('_id.' + field for field in Location._fields), repeat(1)),
        )
        # pylint: enable=no-member, protected_access

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

        self.ignore_write_events_on_courses = []

    def compute_metadata_inheritance_tree(self, location):
        '''
        TODO (cdodge) This method can be deleted when the 'split module store' work has been completed
        '''
        # get all collections in the course, this query should not return any leaf nodes
        # note this is a bit ugly as when we add new categories of containers, we have to add it here

        block_types_with_children = set(name for name, class_ in XBlock.load_classes() if getattr(class_, 'has_children', False))
        query = {'_id.org': location.org,
                 '_id.course': location.course,
                 '_id.category': {'$in': list(block_types_with_children)}
                 }
        # we just want the Location, children, and inheritable metadata
        record_filter = {'_id': 1, 'definition.children': 1}

        # just get the inheritable metadata since that is all we need for the computation
        # this minimizes both data pushed over the wire
        for field_name in InheritanceMixin.fields:
            record_filter['metadata.{0}'.format(field_name)] = 1

        # call out to the DB
        resultset = self.collection.find(query, record_filter)

        results_by_url = {}
        root = None

        # now go through the results and order them by the location url
        for result in resultset:
            location = Location(result['_id'])
            # We need to collate between draft and non-draft
            # i.e. draft verticals will have draft children but will have non-draft parents currently
            location = location.replace(revision=None)
            location_url = location.url()
            if location_url in results_by_url:
                existing_children = results_by_url[location_url].get('definition', {}).get('children', [])
                additional_children = result.get('definition', {}).get('children', [])
                total_children = existing_children + additional_children
                results_by_url[location_url].setdefault('definition', {})['children'] = total_children
            results_by_url[location.url()] = result
            if location.category == 'course':
                root = location.url()

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
        """
        Generate a pymongo in query for finding the items and return the payloads
        """
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
        location = Location(item['location'])
        data_dir = getattr(item, 'data_dir', location.course)
        root = self.fs_root / data_dir

        root.makedirs_p()  # create directory if it doesn't exist

        resource_fs = OSFS(root)

        cached_metadata = {}
        if apply_cached_metadata:
            cached_metadata = self.get_cached_metadata_inheritance_tree(location)

        services = {}
        if self.i18n_service:
            services["i18n"] = self.i18n_service

        # TODO (cdodge): When the 'split module store' work has been completed, we should remove
        # the 'metadata_inheritance_tree' parameter
        system = CachingDescriptorSystem(
            modulestore=self,
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
        course_filter = Location(category="course")
        return [
            course
            for course
            in self.get_items(CourseKey.from_string(course.id))
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

    def get_course(self, course_id, depth=None):
        """
        Get the course with the given courseid (org/course/run)
        """
        assert(isinstance(course_id, SlashSeparatedCourseKey))
        id_components = Location('i4x', course_id.org, course_id.course, 'course', course_id.run)
        try:
            return self.get_item(Location(id_components), depth=depth)
        except ItemNotFoundError:
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

    def get_items(self, course_id, settings=None, content=None, **kwargs):
        """
        Returns:
            list of XModuleDescriptor instances for the matching items within the course with
            the given course_id

        NOTE: don't use this to look for courses
        as the course_id is required. Use get_courses.

        Args:
            course_id (CourseKey): the course identifier
            settings (dict): fields to look for which have settings scope. Follows same syntax
                and rules as kwargs below
            content (dict): fields to look for which have content scope. Follows same syntax and
                rules as kwargs below.
            kwargs (key=value): what to look for within the course.
                Common qualifiers are ``category`` or any field name. if the target field is a list,
                then it searches for the given value in the list not list equivalence.
                Substring matching pass a regex object.
                For this modulestore, ``name`` and ``revision`` are commonly provided keys (Location based stores)
                This modulestore does not allow searching dates by comparison or edited_by, previous_version,
                update_version info.
        """
        query = SON()
        query['_id.tag'] = 'i4x'
        query['_id.org'] = course_id.org
        query['_id.course'] = course_id.course
        for field in ['category', 'name', 'revision']:
            if field in kwargs:
                query['_id.' + field] = kwargs.pop(field)

        for key, value in (settings or {}).iteritems():
            query['metadata.' + key] = value
        for key, value in (content or {}).iteritems():
            query['definition.data.' + key] = value
        if 'children' in kwargs:
            query['definition.children'] = kwargs.pop('children')

        query.update(kwargs)
        items = self.collection.find(
            query,
            sort=[('_id.revision', pymongo.ASCENDING)],
        )

        modules = self._load_items(list(items))
        return modules

    def create_course(self, course_id, definition_data=None, metadata=None, runtime=None):
        """
        Create a course with the given course_id.
        Raises InvalidLocationError if an existing course with this org/name is found.
        """
        if isinstance(course_id, Location):
            location = course_id
            if location.category != 'course':
                raise ValueError(u"Course roots must be of category 'course': {}".format(unicode(location)))
        else:
            location = Location('i4x', course_id.org, course_id.course, 'course', course_id.run)

        # Check if a course with this org/run has been defined before
        # dhm: this query breaks the abstraction, but I'll fix it when I do my suspended refactoring of this
        # file for new locators. get_items should accept a query rather than requiring it be a legal location
        course_search_location = bson.son.SON({
            '_id.tag': 'i4x',
            # cannot pass regex to Location constructor; thus this hack
            # pylint: disable=E1101
            '_id.org': course_id.org,
            # pylint: disable=E1101
            '_id.course': course_id.course,
            '_id.category': 'course',
        })
        courses = modulestore().collection.find(course_search_location, fields=('_id'))
        if courses.count() > 0:
            raise InvalidLocationError()
        course = self.create_and_save_xmodule(location, definition_data, metadata, runtime)

        # clone a default 'about' overview module as well
        about_location = location.replace(
            category='about',
            name='overview'
        )
        overview_template = AboutDescriptor.get_template('overview.yaml')
        self.create_and_save_xmodule(
            about_location,
            system=course.system,
            definition_data=overview_template.get('data')
        )

        return course

    def create_xmodule(self, location, definition_data=None, metadata=None, system=None, fields={}):
        """
        Create the new xmodule but don't save it. Returns the new module.

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param system: if you already have an xblock from the course, the xblock.runtime value
        """
        if not isinstance(location, Location):
            location = Location(location)
        # differs from split mongo in that I believe most of this logic should be above the persistence
        # layer but added it here to enable quick conversion. I'll need to reconcile these.
        if metadata is None:
            metadata = {}

        if definition_data is None:
            definition_data = {}

        if system is None:
            services = {}
            if self.i18n_service:
                services["i18n"] = self.i18n_service

            system = CachingDescriptorSystem(
                modulestore=self,
                module_data={},
                default_class=self.default_class,
                resources_fs=None,
                error_tracker=self.error_tracker,
                render_template=self.render_template,
                cached_metadata={},
                mixins=self.xblock_mixins,
                select=self.xblock_select,
                services=services,
            )
        xblock_class = system.load_block_type(location.category)
        dbmodel = self._create_new_field_data(location.category, location, definition_data, metadata)
        xmodule = system.construct_xblock_from_class(
            xblock_class,
            # We're loading a descriptor, so student_id is meaningless
            # We also don't have separate notions of definition and usage ids yet,
            # so we use the location for both.
            ScopeIds(None, location.category, location, location),
            dbmodel,
        )
        for key, value in fields.iteritems():
            setattr(xmodule, key, value)
        # decache any pending field settings from init
        xmodule.save()
        return xmodule

    def create_and_save_xmodule(self, location, definition_data=None, metadata=None, system=None,
                                fields={}):
        """
        Create the new xmodule and save it. Does not return the new module because if the caller
        will insert it as a child, it's inherited metadata will completely change. The difference
        between this and just doing create_xmodule and update_item is this ensures static_tabs get
        pointed to by the course.

        :param location: a Location--must have a category
        :param definition_data: can be empty. The initial definition_data for the kvs
        :param metadata: can be empty, the initial metadata for the kvs
        :param system: if you already have an xblock from the course, the xblock.runtime value
        """
        # differs from split mongo in that I believe most of this logic should be above the persistence
        # layer but added it here to enable quick conversion. I'll need to reconcile these.
        new_object = self.create_xmodule(location, definition_data, metadata, system, fields)
        location = new_object.location
        self.update_item(new_object, allow_not_found=True)

        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        # TODO move this special casing to app tier (similar to attaching new element to parent)
        if location.category == 'static_tab':
            course = self._get_course_for_item(location)
            existing_tabs = course.tabs or []
            existing_tabs.append({
                'type': 'static_tab',
                'name': new_object.display_name,
                'url_slug': new_object.location.name
            })
            course.tabs = existing_tabs
            self.update_item(course)

        return new_object

    def fire_updated_modulestore_signal(self, course_id, location):
        """
        Send a signal using `self.modulestore_update_signal`, if that has been set
        """
        if self.modulestore_update_signal is not None:
            self.modulestore_update_signal.send(self, modulestore=self, course_id=course_id,
                                                location=location)

    def _get_course_for_item(self, location, depth=0):
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
        from nose.tools import set_trace; set_trace()
        course_search_location = Location('i4x', location.org, location.course, 'course', None)
        courses = self.get_items(CourseKey.from_string(course_search_location.course_id))

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
            {'_id': namedtuple_to_son(Location(location))},
            {'$set': update},
            multi=False,
            upsert=True,
            # Must include this to avoid the django debug toolbar (which defines the deprecated "safe=False")
            # from overriding our default value set in the init method.
            safe=self.collection.safe
        )
        if result['n'] == 0:
            raise ItemNotFoundError(location)

    def update_item(self, xblock, user=None, allow_not_found=False):
        """
        Update the persisted version of xblock to reflect its current values.

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        try:
            definition_data = xblock.get_explicitly_set_fields_by_scope()
            payload = {
                'definition.data': definition_data,
                'metadata': own_metadata(xblock),
            }
            if xblock.has_children:
                # convert all to urls
                xblock.children = [child.url() if isinstance(child, Location) else child
                                   for child in xblock.children]
                payload.update({'definition.children': xblock.children})
            self._update_single_item(xblock.location, payload)
            # for static tabs, their containing course also records their display name
            if xblock.category == 'static_tab':
                course = self._get_course_for_item(xblock.location)
                # find the course's reference to this tab and update the name.
                for tab in course.tabs:
                    if tab.get('url_slug') == xblock.location.name:
                        # only update if changed
                        if tab['name'] != xblock.display_name:
                            tab['name'] = xblock.display_name
                            self.update_item(course, user)
                            break

            # recompute (and update) the metadata inheritance tree which is cached
            # was conditional on children or metadata having changed before dhm made one update to rule them all
            self.refresh_cached_metadata_inheritance_tree(xblock.location)
            # fire signal that we've written to DB
            self.fire_updated_modulestore_signal(get_course_id_no_run(xblock.location), xblock.location)
        except ItemNotFoundError:
            if not allow_not_found:
                raise

    # pylint: disable=unused-argument
    def delete_item(self, location, **kwargs):
        """
        Delete an item from this modulestore

        location: Something that can be passed to Location
        """
        # pylint: enable=unused-argument
        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if location.category == 'static_tab':
            item = self.get_item(location)
            course = self._get_course_for_item(item.location)
            existing_tabs = course.tabs or []
            course.tabs = [tab for tab in existing_tabs if tab.get('url_slug') != location.name]
            self.update_item(course, '**replace_user**')

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
        return [Location(i['_id']) for i in items]

    def get_modulestore_type(self, course_id):
        """
        Returns an enumeration-like type reflecting the type of this modulestore
        The return can be one of:
        "xml" (for XML based courses),
        "mongo" for old-style MongoDB backed courses,
        "split" for new-style split MongoDB backed courses.
        """
        return MONGO_MODULESTORE_TYPE

    def get_orphans(self, course_location, _branch):
        """
        Return an array all of the locations for orphans in the course.
        """
        detached_categories = [name for name, __ in XBlock.load_tagged_classes("detached")]
        all_items = self.collection.find({
            '_id.org': course_location.org,
            '_id.course': course_location.course,
            '_id.category': {'$nin': detached_categories}
        })
        all_reachable = set()
        item_locs = set()
        for item in all_items:
            if item['_id']['category'] != 'course':
                item_locs.add(Location(item['_id']).replace(revision=None).url())
            all_reachable = all_reachable.union(item.get('definition', {}).get('children', []))
        item_locs -= all_reachable
        return list(item_locs)

    def get_courses_for_wiki(self, wiki_slug):
        """
        Return the list of courses which use this wiki_slug
        :param wiki_slug: the course wiki root slug
        :return: list of course locations
        """
        courses = self.collection.find({'definition.data.wiki_slug': wiki_slug})
        return [Location(course['_id']) for course in courses]

    def _create_new_field_data(self, _category, _location, definition_data, metadata):
        """
        To instantiate a new xmodule which will be saved latter, set up the dbModel and kvs
        """
        kvs = MongoKeyValueStore(
            definition_data,
            [],
            metadata,
        )

        field_data = KvsFieldData(kvs)
        return field_data
