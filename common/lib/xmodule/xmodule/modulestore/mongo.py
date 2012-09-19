import pymongo

from bson.son import SON
from fs.osfs import OSFS
from itertools import repeat
from path import path

from importlib import import_module
from xmodule.errortracker import null_error_tracker
from xmodule.x_module import XModuleDescriptor
from xmodule.mako_module import MakoDescriptorSystem

from . import ModuleStoreBase, Location
from .exceptions import (ItemNotFoundError,
                         NoPathToItem, DuplicateItemError)

# TODO (cpennington): This code currently operates under the assumption that
# there is only one revision for each item. Once we start versioning inside the CMS,
# that assumption will have to change


class CachingDescriptorSystem(MakoDescriptorSystem):
    """
    A system that has a cache of module json that it will use to load modules
    from, with a backup of calling to the underlying modulestore for more data
    """
    def __init__(self, modulestore, module_data, default_class, resources_fs,
                 error_tracker, render_template):
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
                self.load_item, resources_fs, error_tracker, render_template)
        self.modulestore = modulestore
        self.module_data = module_data
        self.default_class = default_class

    def load_item(self, location):
        location = Location(location)
        json_data = self.module_data.get(location)
        if json_data is None:
            return self.modulestore.get_item(location)
        else:
            # TODO (vshnayder): metadata inheritance is somewhat broken because mongo, doesn't
            # always load an entire course.  We're punting on this until after launch, and then
            # will build a proper course policy framework.
            return XModuleDescriptor.load_from_json(json_data, self, self.default_class)


def location_to_query(location):
    """
    Takes a Location and returns a SON object that will query for that location.
    Fields in location that are None are ignored in the query
    """
    query = SON()
    # Location dict is ordered by specificity, and SON
    # will preserve that order for queries
    for key, val in Location(location).dict().iteritems():
        if val is not None:
            query['_id.{key}'.format(key=key)] = val

    return query


class MongoModuleStore(ModuleStoreBase):
    """
    A Mongodb backed ModuleStore
    """

    # TODO (cpennington): Enable non-filesystem filestores
    def __init__(self, host, db, collection, fs_root, render_template,
                 port=27017, default_class=None,
                 error_tracker=null_error_tracker):

        ModuleStoreBase.__init__(self)

        self.collection = pymongo.connection.Connection(
            host=host,
            port=port
        )[db][collection]

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

    def _clean_item_data(self, item):
        """
        Renames the '_id' field in item to 'location'
        """
        item['location'] = item['_id']
        del item['_id']

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

            # Load all children by id. See
            # http://www.mongodb.org/display/DOCS/Advanced+Queries#AdvancedQueries-%24or
            # for or-query syntax
            if children:
                to_process = list(self.collection.find(
                    {'_id': {'$in': [Location(child).dict() for child in children]}}))
            else:
                to_process = []
            # If depth is None, then we just recurse until we hit all the descendents
            if depth is not None:
                depth -= 1

        return data

    def _load_item(self, item, data_cache):
        """
        Load an XModuleDescriptor from item, using the children stored in data_cache
        """
        data_dir = item.get('metadata', {}).get('data_dir', item['location']['course'])
        root = self.fs_root / data_dir
        
        if not root.isdir():
            root.mkdir()

        resource_fs = OSFS(root)

        system = CachingDescriptorSystem(
            self,
            data_cache,
            self.default_class,
            resource_fs,
            self.error_tracker,
            self.render_template,
        )
        return system.load_item(item['location'])

    def _load_items(self, items, depth=0):
        """
        Load a list of xmodules from the data in items, with children cached up
        to specified depth
        """
        data_cache = self._cache_children(items, depth)

        return [self._load_item(item, data_cache) for item in items]

    def get_courses(self):
        '''
        Returns a list of course descriptors.
        '''
        # TODO (vshnayder): Why do I have to specify i4x here?
        course_filter = Location("i4x", category="course")
        return self.get_items(course_filter)

    def _find_one(self, location):
        '''Look for a given location in the collection.  If revision is not
        specified, returns the latest.  If the item is not present, raise
        ItemNotFoundError.
        '''
        item = self.collection.find_one(
            location_to_query(location),
            sort=[('revision', pymongo.ASCENDING)],
        )
        if item is None:
            raise ItemNotFoundError(location)
        return item

    def get_item(self, location, depth=0):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the item with the most
        recent revision.

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
        return self._load_items([item], depth)[0]

    def get_instance(self, course_id, location):
        """
        TODO (vshnayder): implement policy tracking in mongo.
        For now, just delegate to get_item and ignore policy.
        """
        return self.get_item(location)

    def get_items(self, location, depth=0):
        items = self.collection.find(
            location_to_query(location),
            sort=[('revision', pymongo.ASCENDING)],
        )

        return self._load_items(list(items), depth)

    # TODO (cpennington): This needs to be replaced by clone_item as soon as we allow
    # creation of items from the cms
    def create_item(self, location):
        """
        Create an empty item at the specified location.

        If that location already exists, raises a DuplicateItemError

        location: Something that can be passed to Location
        """
        try:
            self.collection.insert({
                '_id': Location(location).dict(),
            })
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateItemError(location)

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """

        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        self.collection.update(
            {'_id': Location(location).dict()},
            {'$set': {'definition.data': data}},

        )

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        children

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """

        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        self.collection.update(
            {'_id': Location(location).dict()},
            {'$set': {'definition.children': children}}
        )

    def update_metadata(self, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """

        # See http://www.mongodb.org/display/DOCS/Updating for
        # atomic update syntax
        self.collection.update(
            {'_id': Location(location).dict()},
            {'$set': {'metadata': metadata}}
        )

    def get_parent_locations(self, location):
        '''Find all locations that are the parents of this location.  Needed
        for path_to_location().

        If there is no data at location in this modulestore, raise
            ItemNotFoundError.

        returns an iterable of things that can be passed to Location.  This may
        be empty if there are no parents.
        '''
        location = Location.ensure_fully_specified(location)
        # Check that it's actually in this modulestore.
        item = self._find_one(location)
        # now get the parents
        items = self.collection.find({'definition.children': location.url()},
                                    {'_id': True})
        return [i['_id'] for i in items]

    def get_errored_courses(self):
        """
        This function doesn't make sense for the mongo modulestore, as courses
        are loaded on demand, rather than up front
        """
        return {}
