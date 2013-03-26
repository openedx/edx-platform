import pymongo

from mock import Mock
from nose.tools import assert_equals, assert_raises, assert_not_equals, with_setup, assert_false
from pprint import pprint

from xmodule.modulestore import Location
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.xml_importer import import_from_xml

from .test_modulestore import check_path_to_location
from . import DATA_DIR


HOST = 'localhost'
PORT = 27017
DB = 'test'
COLLECTION = 'modulestore'
FS_ROOT = DATA_DIR  # TODO (vshnayder): will need a real fs_root for testing load_item
DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'
RENDER_TEMPLATE = lambda t_n, d, ctx=None, nsp='main': ''


class TestMongoModuleStore(object):
    '''Tests!'''
    @classmethod
    def setupClass(cls):
        cls.connection = pymongo.connection.Connection(HOST, PORT)
        cls.connection.drop_database(DB)

        # NOTE: Creating a single db for all the tests to save time.  This
        # is ok only as long as none of the tests modify the db.
        # If (when!) that changes, need to either reload the db, or load
        # once and copy over to a tmp db for each test.
        cls.store = cls.initdb()

    @classmethod
    def teardownClass(cls):
        pass

    @staticmethod
    def initdb():
        # connect to the db
        store = MongoModuleStore(HOST, DB, COLLECTION, FS_ROOT, RENDER_TEMPLATE, default_class=DEFAULT_CLASS)
        # Explicitly list the courses to load (don't want the big one)
        courses = ['toy', 'simple']
        import_from_xml(store, DATA_DIR, courses)
        return store

    @staticmethod
    def destroy_db(connection):
        # Destroy the test db.
        connection.drop_database(DB)

    def setUp(self):
        # make a copy for convenience
        self.connection = TestMongoModuleStore.connection

    def tearDown(self):
        pass

    def test_init(self):
        '''Make sure the db loads, and print all the locations in the db.
        Call this directly from failing tests to see what is loaded'''
        ids = list(self.connection[DB][COLLECTION].find({}, {'_id': True}))

        pprint([Location(i['_id']).url() for i in ids])

    def test_get_courses(self):
        '''Make sure the course objects loaded properly'''
        courses = self.store.get_courses()
        assert_equals(len(courses), 2)
        courses.sort(key=lambda c: c.id)
        assert_equals(courses[0].id, 'edX/simple/2012_Fall')
        assert_equals(courses[1].id, 'edX/toy/2012_Fall')

    def test_loads(self):
        assert_not_equals(
            self.store.get_item("i4x://edX/toy/course/2012_Fall"),
            None)

        assert_not_equals(
            self.store.get_item("i4x://edX/simple/course/2012_Fall"),
            None)

        assert_not_equals(
            self.store.get_item("i4x://edX/toy/video/Welcome"),
            None)

    def test_find_one(self):
        assert_not_equals(
            self.store._find_one(Location("i4x://edX/toy/course/2012_Fall")),
            None)

        assert_not_equals(
            self.store._find_one(Location("i4x://edX/simple/course/2012_Fall")),
            None)

        assert_not_equals(
            self.store._find_one(Location("i4x://edX/toy/video/Welcome")),
            None)

    def test_path_to_location(self):
        '''Make sure that path_to_location works'''
        check_path_to_location(self.store)

    def test_metadata_inheritance_query_count(self):
        '''
        When retrieving items from mongo, we should only query the cache a number of times
        equal to the number of courses being retrieved from.

        We should also not query
        '''
        self.store.metadata_inheritance_cache = Mock()
        get_many = self.store.metadata_inheritance_cache.get_many
        set_many = self.store.metadata_inheritance_cache.set_many
        get_many.return_value = {('edX', 'toy'): {}}

        self.store.get_item(Location("i4x://edX/toy/course/2012_Fall"), depth=0)
        assert_false(get_many.called)
        assert_false(set_many.called)
        get_many.reset_mock()

        self.store.get_item(Location("i4x://edX/toy/course/2012_Fall"), depth=3)
        get_many.assert_called_with([('edX', 'toy')])
        assert_equals(0, set_many.call_count)
        get_many.reset_mock()

        self.store.get_items(Location('i4x', 'edX', None, 'course', None), depth=0)
        assert_false(get_many.called)
        assert_false(set_many.called)
        get_many.reset_mock()

        self.store.get_items(Location('i4x', 'edX', None, 'course', None), depth=3)
        assert_equals(1, get_many.call_count)
        assert_equals([('edX', 'simple'), ('edX', 'toy')], sorted(get_many.call_args[0][0]))
        assert_equals(1, set_many.call_count)
        assert_equals([('edX', 'simple')], sorted(set_many.call_args[0][0].keys()))
        get_many.reset_mock()

        self.store.get_items(Location('i4x', 'edX', None, None, None), depth=0)
        assert_equals(1, get_many.call_count)
        assert_equals([('edX', 'simple'), ('edX', 'toy')], sorted(get_many.call_args[0][0]))
        assert_equals(1, set_many.call_count)
        assert_equals([('edX', 'simple')], sorted(set_many.call_args[0][0].keys()))
        get_many.reset_mock()

    def test_metadata_inheritance_query_count_forced_refresh(self):
        self.store.metadata_inheritance_cache = Mock()
        get_many = self.store.metadata_inheritance_cache.get_many
        set_many = self.store.metadata_inheritance_cache.set_many
        get_many.return_value = {('edX', 'toy'): {}}

        self.store.get_cached_metadata_inheritance_trees(
            [Location("i4x://edX/toy/course/2012_Fall"), Location("i4x://edX/simple/course/2012_Fall")],
            True
        )
        assert_false(get_many.called)
        assert_equals(1, set_many.call_count)
        assert_equals([('edX', 'simple'), ('edX', 'toy')], sorted(set_many.call_args[0][0].keys()))
