import pymongo
from . import KeyStore
from .exceptions import ItemNotFoundError


class MongoKeyStore(KeyStore):
    """
    A Mongodb backed KeyStore
    """
    def __init__(self, host, db, collection, port=27017):
        self.collection = pymongo.connection.Connection(
            host=host,
            port=port
        )[db][collection]

    def get_children_for_item(self, location):
        item = self.collection.find_one(
            {'location': location.dict()},
            fields={'children': True},
            sort=[('revision', pymongo.ASCENDING)],
        )

        if item is None:
            raise ItemNotFoundError()

        return item['children']
