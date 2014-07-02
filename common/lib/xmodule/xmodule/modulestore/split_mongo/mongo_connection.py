"""
Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
"""
import re
import pymongo
from bson import son
from xmodule.exceptions import HeartbeatFailure

class MongoConnection(object):
    """
    Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
    """
    def __init__(
        self, db, collection, host, port=27017, tz_aware=True, user=None, password=None, **kwargs
    ):
        """
        Create & open the connection, authenticate, and provide pointers to the collections
        """
        self.database = pymongo.database.Database(
            pymongo.MongoClient(
                host=host,
                port=port,
                tz_aware=tz_aware,
                document_class=son.SON,
                **kwargs
            ),
            db
        )

        if user is not None and password is not None:
            self.database.authenticate(user, password)

        self.course_index = self.database[collection + '.active_versions']
        self.structures = self.database[collection + '.structures']
        self.definitions = self.database[collection + '.definitions']

        # every app has write access to the db (v having a flag to indicate r/o v write)
        # Force mongo to report errors, at the expense of performance
        # pymongo docs suck but explanation:
        # http://api.mongodb.org/java/2.10.1/com/mongodb/WriteConcern.html
        self.course_index.write_concern = {'w': 1}
        self.structures.write_concern = {'w': 1}
        self.definitions.write_concern = {'w': 1}

    def heartbeat(self):
        """
        Check that the db is reachable.
        """
        if self.database.connection.alive():
            return True
        else:
            raise HeartbeatFailure("Can't connect to {}".format(self.database.name))

    def get_structure(self, key):
        """
        Get the structure from the persistence mechanism whose id is the given key
        """
        return self.structures.find_one({'_id': key})

    def find_matching_structures(self, query):
        """
        Find the structure matching the query. Right now the query must be a legal mongo query
        :param query: a mongo-style query of {key: [value|{$in ..}|..], ..}
        """
        return self.structures.find(query)

    def insert_structure(self, structure):
        """
        Create the structure in the db
        """
        self.structures.insert(structure)

    def update_structure(self, structure):
        """
        Update the db record for structure
        """
        self.structures.update({'_id': structure['_id']}, structure)

    def get_course_index(self, key, ignore_case=False):
        """
        Get the course_index from the persistence mechanism whose id is the given key
        """
        case_regex = r"(?i)^{}$" if ignore_case else r"{}"
        return self.course_index.find_one(
            son.SON([
                (key_attr, re.compile(case_regex.format(getattr(key, key_attr))))
                for key_attr in ('org', 'course', 'run')
            ])
        )

    def find_matching_course_indexes(self, query):
        """
        Find the course_index matching the query. Right now the query must be a legal mongo query
        :param query: a mongo-style query of {key: [value|{$in ..}|..], ..}
        """
        return self.course_index.find(query)

    def insert_course_index(self, course_index):
        """
        Create the course_index in the db
        """
        self.course_index.insert(course_index)

    def update_course_index(self, course_index):
        """
        Update the db record for course_index
        """
        self.course_index.update(
            son.SON([('org', course_index['org']), ('course', course_index['course']), ('run', course_index['run'])]),
            course_index
        )

    def delete_course_index(self, course_index):
        """
        Delete the course_index from the persistence mechanism whose id is the given course_index
        """
        return self.course_index.remove(son.SON([
            ('org', course_index['org']),
            ('course', course_index['course']),
            ('run', course_index['run'])
        ]))

    def get_definition(self, key):
        """
        Get the definition from the persistence mechanism whose id is the given key
        """
        return self.definitions.find_one({'_id': key})

    def find_matching_definitions(self, query):
        """
        Find the definitions matching the query. Right now the query must be a legal mongo query
        :param query: a mongo-style query of {key: [value|{$in ..}|..], ..}
        """
        return self.definitions.find(query)

    def insert_definition(self, definition):
        """
        Create the definition in the db
        """
        self.definitions.insert(definition)


