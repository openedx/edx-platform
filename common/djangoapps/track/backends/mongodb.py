"""MongoDB event tracker backend."""

from __future__ import absolute_import

import logging

import pymongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from track.backends import BaseBackend


log = logging.getLogger('track.backends.mongodb')


class MongoBackend(BaseBackend):
    """Class for a MongoDB event tracker Backend"""

    def __init__(self, **kwargs):
        """
        Connect to a MongoDB.

        :Parameters:

          - `host`: hostname
          - `port`: port
          - `user`: collection username
          - `password`: collection user password
          - `database`: name of the database
          - `collection`: name of the collection
          - `extra`: parameters to pymongo.MongoClient not listed above

        """

        super(MongoBackend, self).__init__(**kwargs)

        # Extract connection parameters from kwargs

        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 27017)

        user = kwargs.get('user', '')
        password = kwargs.get('password', '')

        db_name = kwargs.get('database', 'track')
        collection_name = kwargs.get('collection', 'events')

        # Other mongo connection arguments
        extra = kwargs.get('extra', {})

        # By default disable write acknowledgments, reducing the time
        # blocking during an insert
        extra['w'] = extra.get('w', 0)

        # Make timezone aware by default
        extra['tz_aware'] = extra.get('tz_aware', True)

        # Connect to database and get collection

        self.connection = MongoClient(
            host=host,
            port=port,
            **extra
        )

        self.collection = self.connection[db_name][collection_name]

        if user or password:
            self.collection.database.authenticate(user, password)

        self._create_indexes()

    def _create_indexes(self):
        # WARNING: The collection will be locked during the index
        # creation. If the collection has a large number of
        # documents in it, the operation can take a long time.

        # TODO: The creation of indexes can be moved to a Django
        # management command or equivalent. There is also an option to
        # run the indexing on the background, without locking.
        self.collection.ensure_index([('time', pymongo.DESCENDING)])
        self.collection.ensure_index('event_type')

    def send(self, event):
        try:
            self.collection.insert(event, manipulate=False)
        except PyMongoError:
            msg = 'Error inserting to MongoDB event tracker backend'
            log.exception(msg)
