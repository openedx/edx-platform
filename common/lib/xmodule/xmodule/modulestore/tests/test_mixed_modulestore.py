# pylint: disable=E0611
from nose.tools import assert_equals, assert_raises, assert_false, \
    assert_true, assert_not_equals
# pylint: enable=E0611
import pymongo
from uuid import uuid4

from xmodule.tests import DATA_DIR
from xmodule.modulestore import Location, MONGO_MODULESTORE_TYPE, XML_MODULESTORE_TYPE
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.xml_importer import import_from_xml

# Mixed modulestore depends on django, so we'll manually configure some django settings
# before importing the module
from django.conf import settings
import unittest
import copy
if not settings.configured:
    settings.configure()

from xmodule.modulestore.mixed import MixedModuleStore


HOST = 'localhost'
PORT = 27017
DB = 'test_mongo_%s' % uuid4().hex[:5]
COLLECTION = 'modulestore'
FS_ROOT = DATA_DIR
DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'
RENDER_TEMPLATE = lambda t_n, d, ctx = None, nsp = 'main': ''

IMPORT_COURSEID = 'MITx/999/2013_Spring'
XML_COURSEID1 = 'edX/toy/2012_Fall'
XML_COURSEID2 = 'edX/simple/2012_Fall'

OPTIONS = {
    'mappings': {
        XML_COURSEID1: 'xml',
        XML_COURSEID2: 'xml',
        IMPORT_COURSEID: 'default'
    },
    'reference_type': 'Location',
    'stores': {
        'xml': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': DATA_DIR,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        },
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'DOC_STORE_CONFIG': {
                'host': HOST,
                'db': DB,
                'collection': COLLECTION,
            },
            'OPTIONS': {
                'default_class': DEFAULT_CLASS,
                'fs_root': DATA_DIR,
                'render_template': RENDER_TEMPLATE,
            }
        }
    }
}


class TestMixedModuleStore(object):
    '''Tests!'''
    @classmethod
    def setupClass(cls):
        """
        Set up the database for testing
        """
        cls.connection = pymongo.MongoClient(
            host=HOST,
            port=PORT,
            tz_aware=True,
        )
        cls.connection.drop_database(DB)
        cls.fake_location = Location(['i4x', 'foo', 'bar', 'vertical', 'baz'])
        cls.import_org, cls.import_course, cls.import_run = IMPORT_COURSEID.split('/')
        # NOTE: Creating a single db for all the tests to save time.  This
        # is ok only as long as none of the tests modify the db.
        # If (when!) that changes, need to either reload the db, or load
        # once and copy over to a tmp db for each test.
        cls.store = cls.initdb()

    @classmethod
    def teardownClass(cls):
        """
        Clear out database after test has completed
        """
        cls.destroy_db(cls.connection)

    @staticmethod
    def initdb():
        """
        Initialize the database and import one test course into it
        """
        # connect to the db
        _options = {}
        _options.update(OPTIONS)
        store = MixedModuleStore(**_options)

        import_from_xml(
            store._get_modulestore_for_courseid(IMPORT_COURSEID),
            DATA_DIR,
            ['toy'],
            target_location_namespace=Location(
                'i4x',
                TestMixedModuleStore.import_org,
                TestMixedModuleStore.import_course,
                'course',
                TestMixedModuleStore.import_run
            )
        )

        return store

    @staticmethod
    def destroy_db(connection):
        """
        Destroy the test db.
        """
        connection.drop_database(DB)

    def setUp(self):
        # make a copy for convenience
        self.connection = TestMixedModuleStore.connection

    def tearDown(self):
        pass

    def test_get_modulestore_type(self):
        """
        Make sure we get back the store type we expect for given mappings
        """
        assert_equals(self.store.get_modulestore_type(XML_COURSEID1), XML_MODULESTORE_TYPE)
        assert_equals(self.store.get_modulestore_type(XML_COURSEID2), XML_MODULESTORE_TYPE)
        assert_equals(self.store.get_modulestore_type(IMPORT_COURSEID), MONGO_MODULESTORE_TYPE)
        # try an unknown mapping, it should be the 'default' store
        assert_equals(self.store.get_modulestore_type('foo/bar/2012_Fall'), MONGO_MODULESTORE_TYPE)

    def test_has_item(self):
        assert_true(self.store.has_item(
            IMPORT_COURSEID, Location(['i4x', self.import_org, self.import_course, 'course', self.import_run])
        ))
        assert_true(self.store.has_item(
            XML_COURSEID1, Location(['i4x', 'edX', 'toy', 'course', '2012_Fall'])
        ))

        # try negative cases
        assert_false(self.store.has_item(
            XML_COURSEID1, Location(['i4x', self.import_org, self.import_course, 'course', self.import_run])
        ))
        assert_false(self.store.has_item(
            IMPORT_COURSEID, Location(['i4x', 'edX', 'toy', 'course', '2012_Fall'])
        ))

    def test_get_item(self):
        with assert_raises(NotImplementedError):
            self.store.get_item(self.fake_location)

    def test_get_instance(self):
        module = self.store.get_instance(
            IMPORT_COURSEID, Location(['i4x', self.import_org, self.import_course, 'course', self.import_run])
        )
        assert_not_equals(module, None)

        module = self.store.get_instance(
            XML_COURSEID1, Location(['i4x', 'edX', 'toy', 'course', '2012_Fall'])
        )
        assert_not_equals(module, None)

        # try negative cases
        with assert_raises(ItemNotFoundError):
            self.store.get_instance(
                XML_COURSEID1, Location(['i4x', self.import_org, self.import_course, 'course', self.import_run])
            )

        with assert_raises(ItemNotFoundError):
            self.store.get_instance(
                IMPORT_COURSEID, Location(['i4x', 'edX', 'toy', 'course', '2012_Fall'])
            )

    def test_get_items(self):
        # NOTE: use get_course if you just want the course. get_items only allows wildcarding of category and name
        modules = self.store.get_items(Location('i4x', None, None, 'course', None), IMPORT_COURSEID)
        assert_equals(len(modules), 1)
        assert_equals(modules[0].location.course, self.import_course)

        modules = self.store.get_items(Location('i4x', None, None, 'course', None), XML_COURSEID1)
        assert_equals(len(modules), 1)
        assert_equals(modules[0].location.course, 'toy')

        modules = self.store.get_items(Location('i4x', 'edX', 'simple', 'course', None), XML_COURSEID2)
        assert_equals(len(modules), 1)
        assert_equals(modules[0].location.course, 'simple')

    def test_update_item(self):
        # FIXME update
        with assert_raises(NotImplementedError):
            self.store.update_item(self.fake_location, '**replace_user**')

    def test_delete_item(self):
        with assert_raises(NotImplementedError):
            self.store.delete_item(self.fake_location)

    def test_get_courses(self):
        # we should have 3 total courses aggregated
        courses = self.store.get_courses()
        assert_equals(len(courses), 3)
        course_ids = []
        for course in courses:
            course_ids.append(course.location.course_id)
        assert_true(IMPORT_COURSEID in course_ids)
        assert_true(XML_COURSEID1 in course_ids)
        assert_true(XML_COURSEID2 in course_ids)

    def test_get_course(self):
        module = self.store.get_course(IMPORT_COURSEID)
        assert_equals(module.location.course, self.import_course)

        module = self.store.get_course(XML_COURSEID1)
        assert_equals(module.location.course, 'toy')

        module = self.store.get_course(XML_COURSEID2)
        assert_equals(module.location.course, 'simple')

    # pylint: disable=E1101
    def test_get_parent_locations(self):
        parents = self.store.get_parent_locations(
            Location(['i4x', self.import_org, self.import_course, 'chapter', 'Overview']),
            IMPORT_COURSEID
        )
        assert_equals(len(parents), 1)
        assert_equals(Location(parents[0]).org, self.import_org)
        assert_equals(Location(parents[0]).course, self.import_course)
        assert_equals(Location(parents[0]).name, self.import_run)

        parents = self.store.get_parent_locations(
            Location(['i4x', 'edX', 'toy', 'chapter', 'Overview']),
            XML_COURSEID1
        )
        assert_equals(len(parents), 1)
        assert_equals(Location(parents[0]).org, 'edX')
        assert_equals(Location(parents[0]).course, 'toy')
        assert_equals(Location(parents[0]).name, '2012_Fall')

class TestMixedMSInit(unittest.TestCase):
    """
    Test initializing w/o a reference_type
    """
    def setUp(self):
        unittest.TestCase.setUp(self)
        options = copy.copy(OPTIONS)
        del options['reference_type']
        self.connection = pymongo.MongoClient(
            host=HOST,
            port=PORT,
            tz_aware=True,
        )
        self.store = MixedModuleStore(**options)

    def test_use_locations(self):
        """
        Test that use_locations defaulted correctly
        """
        self.assertTrue(self.store.use_locations)

