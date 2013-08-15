from __future__ import absolute_import

import logging

import pymongo

from track.backends.base import BaseBackend


log = logging.getLogger('track.backends.mongo')


class MongoBackend(BaseBackend):
    def __init__(self, **options):
        super(MongoBackend, self).__init__(**options)

        uri = self._make_uri(options)

        # By default disable write acknoledgements
        write_concern = options.pop('w', 0)

        db_name = options.pop('database', 'track')
        collection_name = options.pop('database', 'events')

        self.client = pymongo.MongoClient(host=uri, w=write_concern, **options)

        self.collection = self.client[db_name][collection_name]

        self.create_indexes()

    def _make_uri(self, options):
        # Make a MongoDB URI from options

        host = options.pop('host', 'localhost')
        port = options.pop('port', 27017)
        user = options.pop('user', '')
        password = options.pop('password', '')

        uri = 'mongodb://'
        if user or password:
            uri += '{user}:{password}@'.format(user, password)
        uri += '{host}:{port}'.format(host, port)

        return uri

    def create_indexes(self):
        self.collection.create_index([
            ('time', pymongo.DESCENDING),
            ('event_type',),
        ])

    def send(self, event):
        self.collection.insert(event)
