"""
Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
"""
import re
import pymongo
from contracts import check
from xmodule.exceptions import HeartbeatFailure
from xmodule.modulestore.split_mongo import BlockKey
from datetime import tzinfo
import datetime
import pytz


def structure_from_mongo(structure):
    """
    Converts the 'blocks' key from a list [block_data] to a map
        {BlockKey: block_data}.
    Converts 'root' from [block_type, block_id] to BlockKey.
    Converts 'blocks.*.fields.children' from [[block_type, block_id]] to [BlockKey].
    N.B. Does not convert any other ReferenceFields (because we don't know which fields they are at this level).
    """
    check('seq[2]', structure['root'])
    check('list(dict)', structure['blocks'])
    for block in structure['blocks']:
        if 'children' in block['fields']:
            check('list(list[2])', block['fields']['children'])

    structure['root'] = BlockKey(*structure['root'])
    new_blocks = {}
    for block in structure['blocks']:
        if 'children' in block['fields']:
            block['fields']['children'] = [BlockKey(*child) for child in block['fields']['children']]
        new_blocks[BlockKey(block['block_type'], block.pop('block_id'))] = block
    structure['blocks'] = new_blocks

    return structure


def structure_to_mongo(structure):
    """
    Converts the 'blocks' key from a map {BlockKey: block_data} to
        a list [block_data], inserting BlockKey.type as 'block_type'
        and BlockKey.id as 'block_id'.
    Doesn't convert 'root', since namedtuple's can be inserted
        directly into mongo.
    """
    check('BlockKey', structure['root'])
    check('dict(BlockKey: dict)', structure['blocks'])
    for block in structure['blocks'].itervalues():
        if 'children' in block['fields']:
            check('list(BlockKey)', block['fields']['children'])

    new_structure = dict(structure)
    new_structure['blocks'] = []

    for block_key, block in structure['blocks'].iteritems():
        new_block = dict(block)
        new_block.setdefault('block_type', block_key.type)
        new_block['block_id'] = block_key.id
        new_structure['blocks'].append(new_block)

    return new_structure


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
        return structure_from_mongo(self.structures.find_one({'_id': key}))

    def find_structures_by_id(self, ids):
        """
        Return all structures that specified in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        return [structure_from_mongo(structure) for structure in self.structures.find({'_id': {'$in': ids}})]

    def find_structures_derived_from(self, ids):
        """
        Return all structures that were immediately derived from a structure listed in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        return [structure_from_mongo(structure) for structure in self.structures.find({'previous_version': {'$in': ids}})]

    def find_ancestor_structures(self, original_version, block_key):
        """
        Find all structures that originated from ``original_version`` that contain ``block_key``.

        Arguments:
            original_version (str or ObjectID): The id of a structure
            block_key (BlockKey): The id of the block in question
        """
        return [structure_from_mongo(structure) for structure in self.structures.find({
            'original_version': original_version,
            'blocks': {
                '$elemMatch': {
                    'block_id': block_key.id,
                    'block_type': block_key.type,
                    'edit_info.update_version': {'$exists': True},
                }
            }
        })]

    def upsert_structure(self, structure):
        """
        Update the db record for structure, creating that record if it doesn't already exist
        """
        self.structures.update({'_id': structure['_id']}, structure_to_mongo(structure), upsert=True)

    def get_course_index(self, key, ignore_case=False):
        """
        Get the course_index from the persistence mechanism whose id is the given key
        """
        case_regex = ur"(?i)^{}$" if ignore_case else ur"{}"
        return self.course_index.find_one(
            {
                key_attr: re.compile(case_regex.format(getattr(key, key_attr)))
                for key_attr in ('org', 'course', 'run')
            }
        )

    def find_matching_course_indexes(self, branch=None, search_targets=None):
        """
        Find the course_index matching particular conditions.

        Arguments:
            branch: If specified, this branch must exist in the returned courses
            search_targets: If specified, this must be a dictionary specifying field values
                that must exist in the search_targets of the returned courses
        """
        query = {}
        if branch is not None:
            query['versions.{}'.format(branch)] = {'$exists': True}

        if search_targets:
            for key, value in search_targets.iteritems():
                query['search_targets.{}'.format(key)] = value

        return self.course_index.find(query)

    def insert_course_index(self, course_index):
        """
        Create the course_index in the db
        """
        course_index['last_update'] = datetime.datetime.now(pytz.utc)
        self.course_index.insert(course_index)

    def update_course_index(self, course_index, from_index=None):
        """
        Update the db record for course_index.

        Arguments:
            from_index: If set, only update an index if it matches the one specified in `from_index`.
        """
        if from_index:
            query = {"_id": from_index["_id"]}
            # last_update not only tells us when this course was last updated but also helps
            # prevent collisions
            if 'last_update' in from_index:
                query['last_update'] = from_index['last_update']
        else:
            query = {
                'org': course_index['org'],
                'course': course_index['course'],
                'run': course_index['run'],
            }
        course_index['last_update'] = datetime.datetime.now(pytz.utc)
        self.course_index.update(query, course_index, upsert=False,)

    def delete_course_index(self, course_index):
        """
        Delete the course_index from the persistence mechanism whose id is the given course_index
        """
        return self.course_index.remove({
            'org': course_index['org'],
            'course': course_index['course'],
            'run': course_index['run'],
        })

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

    def ensure_indexes(self):
        """
        Ensure that all appropriate indexes are created that are needed by this modulestore, or raise
        an exception if unable to.

        This method is intended for use by tests and administrative commands, and not
        to be run during server startup.
        """
        self.course_index.create_index(
            [
                ('org', pymongo.ASCENDING),
                ('course', pymongo.ASCENDING),
                ('run', pymongo.ASCENDING)
            ],
            unique=True
        )

