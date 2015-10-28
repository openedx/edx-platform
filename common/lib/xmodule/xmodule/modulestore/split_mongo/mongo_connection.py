"""
Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
"""
import datetime
import cPickle as pickle
import math
import zlib
import pymongo
import pytz
import re
from contextlib import contextmanager
from time import time

# Import this just to export it
from pymongo.errors import DuplicateKeyError  # pylint: disable=unused-import
from django.core.cache import get_cache, InvalidCacheBackendError
import dogstats_wrapper as dog_stats_api

from contracts import check, new_contract
from mongodb_proxy import autoretry_read, MongoProxy
from xmodule.exceptions import HeartbeatFailure
from xmodule.modulestore import BlockData
from xmodule.modulestore.split_mongo import BlockKey


new_contract('BlockData', BlockData)


def round_power_2(value):
    """
    Return value rounded up to the nearest power of 2.
    """
    if value == 0:
        return 0

    return math.pow(2, math.ceil(math.log(value, 2)))


class Tagger(object):
    """
    An object used by :class:`QueryTimer` to allow timed code blocks
    to add measurements and tags to the timer.
    """
    def __init__(self, default_sample_rate):
        self.added_tags = []
        self.measures = []
        self.sample_rate = default_sample_rate

    def measure(self, name, size):
        """
        Record a measurement of the timed data. This would be something to
        indicate the size of the value being timed.

        Arguments:
            name: The name of the measurement.
            size (float): The size of the measurement.
        """
        self.measures.append((name, size))

    def tag(self, **kwargs):
        """
        Add tags to the timer.

        Arguments:
            **kwargs: Each keyword is treated as a tag name, and the
                value of the argument is the tag value.
        """
        self.added_tags.extend(kwargs.items())

    @property
    def tags(self):
        """
        Return all tags for this (this includes any tags added with :meth:`tag`,
        and also all of the added measurements, bucketed into powers of 2).
        """
        return [
            '{}:{}'.format(name, round_power_2(size))
            for name, size in self.measures
        ] + [
            '{}:{}'.format(name, value)
            for name, value in self.added_tags
        ]


class QueryTimer(object):
    """
    An object that allows timing a block of code while also recording measurements
    about that code.
    """
    def __init__(self, metric_base, sample_rate=1):
        """
        Arguments:
            metric_base: The prefix to be used for all queries captured
            with this :class:`QueryTimer`.
        """
        self._metric_base = metric_base
        self._sample_rate = sample_rate

    @contextmanager
    def timer(self, metric_name, course_context):
        """
        Contextmanager which acts as a timer for the metric ``metric_name``,
        but which also yields a :class:`Tagger` object that allows the timed block
        of code to add tags and quantity measurements. Tags are added verbatim to the
        timer output. Measurements are recorded as histogram measurements in their own,
        and also as bucketed tags on the timer measurement.

        Arguments:
            metric_name: The name used to aggregate all of these metrics.
            course_context: The course which the query is being made for.
        """
        tagger = Tagger(self._sample_rate)
        metric_name = "{}.{}".format(self._metric_base, metric_name)

        start = time()
        try:
            yield tagger
        finally:
            end = time()
            tags = tagger.tags
            tags.append('course:{}'.format(course_context))
            for name, size in tagger.measures:
                dog_stats_api.histogram(
                    '{}.{}'.format(metric_name, name),
                    size,
                    timestamp=end,
                    tags=[tag for tag in tags if not tag.startswith('{}:'.format(metric_name))],
                    sample_rate=tagger.sample_rate,
                )
            dog_stats_api.histogram(
                '{}.duration'.format(metric_name),
                end - start,
                timestamp=end,
                tags=tags,
                sample_rate=tagger.sample_rate,
            )
            dog_stats_api.increment(
                metric_name,
                timestamp=end,
                tags=tags,
                sample_rate=tagger.sample_rate,
            )


TIMER = QueryTimer(__name__, 0.01)


def structure_from_mongo(structure, course_context=None):
    """
    Converts the 'blocks' key from a list [block_data] to a map
        {BlockKey: block_data}.
    Converts 'root' from [block_type, block_id] to BlockKey.
    Converts 'blocks.*.fields.children' from [[block_type, block_id]] to [BlockKey].
    N.B. Does not convert any other ReferenceFields (because we don't know which fields they are at this level).

    Arguments:
        structure: The document structure to convert
        course_context (CourseKey): For metrics gathering, the CourseKey
            for the course that this data is being processed for.
    """
    with TIMER.timer('structure_from_mongo', course_context) as tagger:
        tagger.measure('blocks', len(structure['blocks']))

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
            new_blocks[BlockKey(block['block_type'], block.pop('block_id'))] = BlockData(**block)
        structure['blocks'] = new_blocks

        return structure


def structure_to_mongo(structure, course_context=None):
    """
    Converts the 'blocks' key from a map {BlockKey: block_data} to
        a list [block_data], inserting BlockKey.type as 'block_type'
        and BlockKey.id as 'block_id'.
    Doesn't convert 'root', since namedtuple's can be inserted
        directly into mongo.
    """
    with TIMER.timer('structure_to_mongo', course_context) as tagger:
        tagger.measure('blocks', len(structure['blocks']))

        check('BlockKey', structure['root'])
        check('dict(BlockKey: BlockData)', structure['blocks'])
        for block in structure['blocks'].itervalues():
            if 'children' in block.fields:
                check('list(BlockKey)', block.fields['children'])

        new_structure = dict(structure)
        new_structure['blocks'] = []

        for block_key, block in structure['blocks'].iteritems():
            new_block = dict(block.to_storable())
            new_block.setdefault('block_type', block_key.type)
            new_block['block_id'] = block_key.id
            new_structure['blocks'].append(new_block)

        return new_structure


class CourseStructureCache(object):
    """
    Wrapper around django cache object to cache course structure objects.
    The course structures are pickled and compressed when cached.

    If the 'course_structure_cache' doesn't exist, then don't do anything for
    for set and get.
    """
    def __init__(self):
        self.no_cache_found = False
        try:
            self.cache = get_cache('course_structure_cache')
        except InvalidCacheBackendError:
            self.no_cache_found = True

    def get(self, key, course_context=None):
        """Pull the compressed, pickled struct data from cache and deserialize."""
        if self.no_cache_found:
            return None

        with TIMER.timer("CourseStructureCache.get", course_context) as tagger:
            compressed_pickled_data = self.cache.get(key)
            tagger.tag(from_cache=str(compressed_pickled_data is not None).lower())

            if compressed_pickled_data is None:
                # Always log cache misses, because they are unexpected
                tagger.sample_rate = 1
                return None

            tagger.measure('compressed_size', len(compressed_pickled_data))

            pickled_data = zlib.decompress(compressed_pickled_data)
            tagger.measure('uncompressed_size', len(pickled_data))

            return pickle.loads(pickled_data)

    def set(self, key, structure, course_context=None):
        """Given a structure, will pickle, compress, and write to cache."""
        if self.no_cache_found:
            return None

        with TIMER.timer("CourseStructureCache.set", course_context) as tagger:
            pickled_data = pickle.dumps(structure, pickle.HIGHEST_PROTOCOL)
            tagger.measure('uncompressed_size', len(pickled_data))

            # 1 = Fastest (slightly larger results)
            compressed_pickled_data = zlib.compress(pickled_data, 1)
            tagger.measure('compressed_size', len(compressed_pickled_data))

            # Stuctures are immutable, so we set a timeout of "never"
            self.cache.set(key, compressed_pickled_data, None)


class MongoConnection(object):
    """
    Segregation of pymongo functions from the data modeling mechanisms for split modulestore.
    """
    def __init__(
        self, db, collection, host, port=27017, tz_aware=True, user=None, password=None,
        asset_collection=None, retry_wait_time=0.1, **kwargs
    ):
        """
        Create & open the connection, authenticate, and provide pointers to the collections
        """
        if kwargs.get('replicaSet') is None:
            kwargs.pop('replicaSet', None)
            mongo_class = pymongo.MongoClient
        else:
            mongo_class = pymongo.MongoReplicaSetClient
        _client = mongo_class(
            host=host,
            port=port,
            tz_aware=tz_aware,
            **kwargs
        )
        self.database = MongoProxy(
            pymongo.database.Database(_client, db),
            wait_time=retry_wait_time
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
            raise HeartbeatFailure("Can't connect to {}".format(self.database.name), 'mongo')

    def get_structure(self, key, course_context=None):
        """
        Get the structure from the persistence mechanism whose id is the given key.

        This method will use a cached version of the structure if it is availble.
        """
        with TIMER.timer("get_structure", course_context) as tagger_get_structure:
            cache = CourseStructureCache()

            structure = cache.get(key, course_context)
            tagger_get_structure.tag(from_cache=str(bool(structure)).lower())
            if not structure:
                # Always log cache misses, because they are unexpected
                tagger_get_structure.sample_rate = 1

                with TIMER.timer("get_structure.find_one", course_context) as tagger_find_one:
                    doc = self.structures.find_one({'_id': key})
                    tagger_find_one.measure("blocks", len(doc['blocks']))
                    structure = structure_from_mongo(doc, course_context)
                    tagger_find_one.sample_rate = 1

                cache.set(key, structure, course_context)

            return structure

    @autoretry_read()
    def find_structures_by_id(self, ids, course_context=None):
        """
        Return all structures that specified in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        with TIMER.timer("find_structures_by_id", course_context) as tagger:
            tagger.measure("requested_ids", len(ids))
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find({'_id': {'$in': ids}})
            ]
            tagger.measure("structures", len(docs))
            return docs

    @autoretry_read()
    def find_structures_derived_from(self, ids, course_context=None):
        """
        Return all structures that were immediately derived from a structure listed in ``ids``.

        Arguments:
            ids (list): A list of structure ids
        """
        with TIMER.timer("find_structures_derived_from", course_context) as tagger:
            tagger.measure("base_ids", len(ids))
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find({'previous_version': {'$in': ids}})
            ]
            tagger.measure("structures", len(docs))
            return docs

    @autoretry_read()
    def find_ancestor_structures(self, original_version, block_key, course_context=None):
        """
        Find all structures that originated from ``original_version`` that contain ``block_key``.

        Arguments:
            original_version (str or ObjectID): The id of a structure
            block_key (BlockKey): The id of the block in question
        """
        with TIMER.timer("find_ancestor_structures", course_context) as tagger:
            docs = [
                structure_from_mongo(structure, course_context)
                for structure in self.structures.find({
                    'original_version': original_version,
                    'blocks': {
                        '$elemMatch': {
                            'block_id': block_key.id,
                            'block_type': block_key.type,
                            'edit_info.update_version': {
                                '$exists': True,
                            },
                        },
                    },
                })
            ]
            tagger.measure("structures", len(docs))
            return docs

    def insert_structure(self, structure, course_context=None):
        """
        Insert a new structure into the database.
        """
        with TIMER.timer("insert_structure", course_context) as tagger:
            tagger.measure("blocks", len(structure["blocks"]))
            self.structures.insert(structure_to_mongo(structure, course_context))

    def get_course_index(self, key, ignore_case=False):
        """
        Get the course_index from the persistence mechanism whose id is the given key
        """
        with TIMER.timer("get_course_index", key):
            if ignore_case:
                query = {
                    key_attr: re.compile(u'^{}$'.format(re.escape(getattr(key, key_attr))), re.IGNORECASE)
                    for key_attr in ('org', 'course', 'run')
                }
            else:
                query = {
                    key_attr: getattr(key, key_attr)
                    for key_attr in ('org', 'course', 'run')
                }
            return self.course_index.find_one(query)

    def find_matching_course_indexes(self, branch=None, search_targets=None, org_target=None, course_context=None):
        """
        Find the course_index matching particular conditions.

        Arguments:
            branch: If specified, this branch must exist in the returned courses
            search_targets: If specified, this must be a dictionary specifying field values
                that must exist in the search_targets of the returned courses
            org_target: If specified, this is an ORG filter so that only course_indexs are
                returned for the specified ORG
        """
        with TIMER.timer("find_matching_course_indexes", course_context):
            query = {}
            if branch is not None:
                query['versions.{}'.format(branch)] = {'$exists': True}

            if search_targets:
                for key, value in search_targets.iteritems():
                    query['search_targets.{}'.format(key)] = value

            if org_target:
                query['org'] = org_target

            return self.course_index.find(query)

    def insert_course_index(self, course_index, course_context=None):
        """
        Create the course_index in the db
        """
        with TIMER.timer("insert_course_index", course_context):
            course_index['last_update'] = datetime.datetime.now(pytz.utc)
            self.course_index.insert(course_index)

    def update_course_index(self, course_index, from_index=None, course_context=None):
        """
        Update the db record for course_index.

        Arguments:
            from_index: If set, only update an index if it matches the one specified in `from_index`.
        """
        with TIMER.timer("update_course_index", course_context):
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

    def delete_course_index(self, course_key):
        """
        Delete the course_index from the persistence mechanism whose id is the given course_index
        """
        with TIMER.timer("delete_course_index", course_key):
            query = {
                key_attr: getattr(course_key, key_attr)
                for key_attr in ('org', 'course', 'run')
            }
            return self.course_index.remove(query)

    def get_definition(self, key, course_context=None):
        """
        Get the definition from the persistence mechanism whose id is the given key
        """
        with TIMER.timer("get_definition", course_context) as tagger:
            definition = self.definitions.find_one({'_id': key})
            tagger.measure("fields", len(definition['fields']))
            tagger.tag(block_type=definition['block_type'])
            return definition

    def get_definitions(self, definitions, course_context=None):
        """
        Retrieve all definitions listed in `definitions`.
        """
        with TIMER.timer("get_definitions", course_context) as tagger:
            tagger.measure('definitions', len(definitions))
            definitions = self.definitions.find({'_id': {'$in': definitions}})
            return definitions

    def insert_definition(self, definition, course_context=None):
        """
        Create the definition in the db
        """
        with TIMER.timer("insert_definition", course_context) as tagger:
            tagger.measure('fields', len(definition['fields']))
            tagger.tag(block_type=definition['block_type'])
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
