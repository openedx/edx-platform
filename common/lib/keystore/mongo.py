import pymongo
from . import KeyStore, Location
from .exceptions import ItemNotFoundError, InsufficientSpecificationError
from xmodule.x_module import XModuleDescriptor


class MongoKeyStore(KeyStore):
    """
    A Mongodb backed KeyStore
    """
    def __init__(self, host, db, collection, port=27017):
        self.collection = pymongo.connection.Connection(
            host=host,
            port=port
        )[db][collection]

        # Force mongo to report errors, at the expense of performance
        self.collection.safe = True

    def get_item(self, location):
        """
        Returns an XModuleDescriptor instance for the item at location

        If no object is found at that location, raises keystore.exceptions.ItemNotFoundError

        Searches for all matches of a partially specifed location, but raises an
        keystore.exceptions.InsufficientSpecificationError if more
        than a single object matches the query.

        location: Something that can be passed to Location
        """
        query = dict(
            ('location.{key}'.format(key=key), val)
            for (key, val)
            in Location(location).dict().items()
            if val is not None
        )
        items = self.collection.find(
            query,
            sort=[('revision', pymongo.ASCENDING)],
            limit=1,
        )
        if items.count() > 1:
            raise InsufficientSpecificationError(location)

        if items.count() == 0:
            raise ItemNotFoundError(location)

        return XModuleDescriptor.load_from_json(items[0], self.get_item)

    def create_item(self, location, editor):
        """
        Create an empty item at the specified location with the supplied editor

        location: Something that can be passed to Location
        """
        self.collection.insert({
            'location': Location(location).dict(),
            'editor': editor
        })

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        self.collection.update(
            {'location': Location(location).dict()},
            {'$set': {'data': data}}
        )

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        data

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        self.collection.update(
            {'location': Location(location).dict()},
            {'$set': {'children': children}}
        )
