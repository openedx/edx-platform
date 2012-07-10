import pymongo
from bson.objectid import ObjectId
from importlib import import_module
from xmodule.x_module import XModuleDescriptor
from xmodule.mako_module import MakoDescriptorSystem
from mitxmako.shortcuts import render_to_string

from . import ModuleStore, Location
from .exceptions import ItemNotFoundError, InsufficientSpecificationError


# TODO (cpennington): This code currently operates under the assumption that
# there is only one revision for each item. Once we start versioning inside the CMS,
# that assumption will have to change


def location_to_query(loc):
    query = {}
    for key, val in Location(loc).dict().iteritems():
        if val is not None:
            query['_id.{key}'.format(key=key)] = val

    return query

class MongoModuleStore(ModuleStore):
    """
    A Mongodb backed ModuleStore
    """
    def __init__(self, host, db, collection, port=27017, default_class=None):
        self.collection = pymongo.connection.Connection(
            host=host,
            port=port
        )[db][collection]

        # Force mongo to report errors, at the expense of performance
        self.collection.safe = True

        module_path, _, class_name = default_class.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        self.default_class = class_

        # TODO (cpennington): Pass a proper resources_fs to the system
        self.system = MakoDescriptorSystem(
            load_item=self.get_item,
            resources_fs=None,
            render_template=render_to_string
        )

    def _load_item(self, item):
        item['location'] = item['_id']
        del item['_id']
        return XModuleDescriptor.load_from_json(item, self.system, self.default_class)

    def get_item(self, location):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the most item with the most
        recent revision

        If any segment of the location is None except revision, raises
            xmodule.modulestore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises xmodule.modulestore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """

        for key, val in Location(location).dict().iteritems():
            if key != 'revision' and val is None:
                raise InsufficientSpecificationError(location)

        item = self.collection.find_one(
            location_to_query(location),
            sort=[('revision', pymongo.ASCENDING)],
        )
        if item is None:
            raise ItemNotFoundError(location)
        return self._load_item(item)

    def get_items(self, location, default_class=None):
        print location_to_query(location)
        items = self.collection.find(
            location_to_query(location),
            sort=[('revision', pymongo.ASCENDING)],
        )

        return [self._load_item(item) for item in items]

    def create_item(self, location):
        """
        Create an empty item at the specified location with the supplied editor

        location: Something that can be passed to Location
        """
        self.collection.insert({
            '_id': Location(location).dict(),
        })

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
        Set the children for the item specified by the location to
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
