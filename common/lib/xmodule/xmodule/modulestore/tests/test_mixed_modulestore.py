import pymongo
from uuid import uuid4
import copy
import ddt
from mock import patch

from xmodule.tests import DATA_DIR
from xmodule.modulestore import Location, MONGO_MODULESTORE_TYPE, SPLIT_MONGO_MODULESTORE_TYPE, \
    XML_MODULESTORE_TYPE
from xmodule.modulestore.exceptions import ItemNotFoundError

from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore.tests.test_location_mapper import LocMapperSetupSansDjango, loc_mapper

# FIXME remove settings
from django.conf import settings
if not settings.configured:
    settings.configure()

from xmodule.modulestore.mixed import MixedModuleStore

@ddt.ddt
class TestMixedModuleStore(LocMapperSetupSansDjango):
    """
    Quasi-superclass which tests Location based apps against both split and mongo dbs (Locator and
    Location-based dbs)
    """
    HOST = 'localhost'
    PORT = 27017
    DB = 'test_mongo_%s' % uuid4().hex[:5]
    COLLECTION = 'modulestore'
    FS_ROOT = DATA_DIR
    DEFAULT_CLASS = 'xmodule.raw_module.RawDescriptor'
    RENDER_TEMPLATE = lambda t_n, d, ctx = None, nsp = 'main': ''
    REFERENCE_TYPE = 'xmodule.modulestore.Location'

    IMPORT_COURSEID = 'MITx/999/2013_Spring'
    XML_COURSEID1 = 'edX/toy/2012_Fall'
    XML_COURSEID2 = 'edX/simple/2012_Fall'

    modulestore_options = {
        'default_class': DEFAULT_CLASS,
        'fs_root': DATA_DIR,
        'render_template': RENDER_TEMPLATE,
    }
    DOC_STORE_CONFIG = {
        'host': HOST,
        'db': DB,
        'collection': COLLECTION,
    }
    OPTIONS = {
        'mappings': {
            XML_COURSEID1: 'xml',
            XML_COURSEID2: 'xml',
            IMPORT_COURSEID: 'default'
        },
        'reference_type': REFERENCE_TYPE,
        'stores': {
            'xml': {
                'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
                'OPTIONS': {
                    'data_dir': DATA_DIR,
                    'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                }
            },
            'direct': {
                'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
            'draft': {
                'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
            'split': {
                'ENGINE': 'xmodule.modulestore.split_mongo.SplitMongoModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            }
        }
    }

    def _compareIgnoreVersion(self, loc1, loc2, msg=None):
        """
        AssertEqual replacement for CourseLocator
        """
        if not (loc1.package_id == loc2.package_id and loc1.branch == loc2.branch and loc1.block_id == loc2.block_id):
            self.fail(self._formatMessage(msg, u"{} != {}".format(unicode(loc1), unicode(loc2))))

    def setUp(self):
        """
        Set up the database for testing
        """
        self.options = getattr(self, 'options', self.OPTIONS)
        self.connection = pymongo.MongoClient(
            host=self.HOST,
            port=self.PORT,
            tz_aware=True,
        )
        self.connection.drop_database(self.DB)
        self.addCleanup(self.connection.drop_database, self.DB)
        self.addCleanup(self.connection.close)
        
        super(TestMixedModuleStore, self).setUp()

        patcher = patch('xmodule.modulestore.mixed.loc_mapper', return_value=LocMapperSetupSansDjango.loc_store)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addTypeEqualityFunc(BlockUsageLocator, '_compareIgnoreVersion')

    def _create_course(self, default, course_location, item_location):
        """
        Create a course w/ one item in the persistence store using the given course & item location.
        NOTE: course_location and item_location must be Location regardless of the app reference type in order
        to cause the right mapping to be created.
        """
        if default == 'split':
            course = self.store.create_course(course_location, store_name=default)
            chapter = self.store.create_item(
                # don't use course_location as it may not be the repr
                course.location, item_location.category, location=item_location, block_id=item_location.name
            )
        else:
            course = self.store.create_course(
                course_location, store_name=default, metadata={'display_name': course_location.name}
            )
            chapter = self.store.create_item(course_location, item_location.category, location=item_location)
        if self.REFERENCE_TYPE == 'xmodule.modulestore.locator.CourseLocator':
            # add_entry is false b/c this is a test that the right thing happened w/o
            # wanting any additional side effects
            lookup_map = loc_mapper().translate_location(
                course_location.course_id, course_location, add_entry_if_missing=False
            )
            self.assertEqual(lookup_map, course.location)
            lookup_map = loc_mapper().translate_location(
                course_location.course_id, item_location, add_entry_if_missing=False
            )
            self.assertEqual(lookup_map, chapter.location)
        else:
            self.assertEqual(course.location, course_location)
            self.assertEqual(chapter.location, item_location)

    def initdb(self, default):
        """
        Initialize the database and create one test course in it
        """
        # set the default modulestore
        self.options['stores']['default'] = self.options['stores'][default]
        self.store = MixedModuleStore(**self.options)
        self.addCleanup(self.store.close_all_connections)

        def generate_location(course_id):
            """
            Generate the locations for the given ids
            """
            org, course, run = course_id.split('/')
            return Location('i4x', org, course, 'course', run)

        self.course_locations = {
             course_id: generate_location(course_id)
             for course_id in [self.IMPORT_COURSEID, self.XML_COURSEID1, self.XML_COURSEID2]
        }
        self.fake_location = Location('i4x', 'foo', 'bar', 'vertical', 'baz')
        self.import_chapter_location = self.course_locations[self.IMPORT_COURSEID].replace(
            category='chapter', name='Overview'
        )
        self.xml_chapter_location = self.course_locations[self.XML_COURSEID1].replace(
            category='chapter', name='Overview'
        )
        # grab old style location b4 possibly converted
        import_location = self.course_locations[self.IMPORT_COURSEID]
        # get Locators and set up the loc mapper if app is Locator based
        if self.REFERENCE_TYPE == 'xmodule.modulestore.locator.CourseLocator':
            self.fake_location = loc_mapper().translate_location('foo/bar/2012_Fall', self.fake_location)
            self.import_chapter_location = loc_mapper().translate_location(
                self.IMPORT_COURSEID, self.import_chapter_location
            )
            self.xml_chapter_location = loc_mapper().translate_location(
                self.XML_COURSEID1, self.xml_chapter_location
            )
            self.course_locations = {
                course_id: loc_mapper().translate_location(course_id, locn)
                for course_id, locn in self.course_locations.iteritems()
            }

        self._create_course(default, import_location, self.import_chapter_location)

    @ddt.data('direct', 'split')
    def test_get_modulestore_type(self, default_ms):
        """
        Make sure we get back the store type we expect for given mappings
        """
        self.initdb(default_ms)
        self.assertEqual(self.store.get_modulestore_type(self.XML_COURSEID1), XML_MODULESTORE_TYPE)
        self.assertEqual(self.store.get_modulestore_type(self.XML_COURSEID2), XML_MODULESTORE_TYPE)
        mongo_ms_type = MONGO_MODULESTORE_TYPE if default_ms == 'direct' else SPLIT_MONGO_MODULESTORE_TYPE
        self.assertEqual(self.store.get_modulestore_type(self.IMPORT_COURSEID), mongo_ms_type)
        # try an unknown mapping, it should be the 'default' store
        self.assertEqual(self.store.get_modulestore_type('foo/bar/2012_Fall'), mongo_ms_type)

    @ddt.data('direct', 'split')
    def test_has_item(self, default_ms):
        self.initdb(default_ms)
        for course_id, course_locn in self.course_locations.iteritems():
            self.assertTrue(self.store.has_item(course_id, course_locn))

        # try negative cases
        self.assertFalse(self.store.has_item(self.XML_COURSEID1, self.course_locations[self.IMPORT_COURSEID]))
        self.assertFalse(self.store.has_item(self.IMPORT_COURSEID, self.course_locations[self.XML_COURSEID1]))

    @ddt.data('direct', 'split')
    def test_get_item(self, default_ms):
        self.initdb(default_ms)
        with self.assertRaises(NotImplementedError):
            self.store.get_item(self.fake_location)

    @ddt.data('direct', 'split')
    def test_get_instance(self, default_ms):
        self.initdb(default_ms)
        for course_id, course_locn in self.course_locations.iteritems():
            self.assertIsNotNone(self.store.get_instance(course_id, course_locn))

        # try negative cases
        with self.assertRaises(ItemNotFoundError):
            self.store.get_instance(self.XML_COURSEID1, self.course_locations[self.IMPORT_COURSEID])
        with self.assertRaises(ItemNotFoundError):
            self.store.get_instance(self.IMPORT_COURSEID, self.course_locations[self.XML_COURSEID1])

    @ddt.data('direct', 'split')
    def test_get_items(self, default_ms):
        self.initdb(default_ms)
        for course_id, course_locn in self.course_locations.iteritems():
            if hasattr(course_locn, 'as_course_locator'):
                locn = course_locn.as_course_locator()
            else:
                locn = course_locn.replace(org=None, course=None, name=None)
            # NOTE: use get_course if you just want the course. get_items is expensive
            modules = self.store.get_items(locn, course_id, qualifiers={'category': 'course'})
            self.assertEqual(len(modules), 1)
            self.assertEqual(modules[0].location, course_locn)

    @ddt.data('direct', 'split')
    def test_update_item(self, default_ms):
        """
        Update should fail for r/o dbs and succeed for r/w ones
        """
        self.initdb(default_ms)
        # try a r/o db
        if self.REFERENCE_TYPE == 'xmodule.modulestore.locator.CourseLocator':
            course_id = self.course_locations[self.XML_COURSEID1]
        else:
            course_id = self.XML_COURSEID1
        course = self.store.get_course(course_id)
        # if following raised, then the test is really a noop, change it
        self.assertFalse(course.show_calculator, "Default changed making test meaningless")
        course.show_calculator = True
        with self.assertRaises(NotImplementedError):
            self.store.update_item(course, None)
        # now do it for a r/w db
        # get_course api's are inconsistent: one takes Locators the other an old style course id
        if hasattr(self.course_locations[self.IMPORT_COURSEID], 'as_course_locator'):
            locn = self.course_locations[self.IMPORT_COURSEID]
        else:
            locn = self.IMPORT_COURSEID
        course = self.store.get_course(locn)
        # if following raised, then the test is really a noop, change it
        self.assertFalse(course.show_calculator, "Default changed making test meaningless")
        course.show_calculator = True
        self.store.update_item(course, None)
        course = self.store.get_course(locn)
        self.assertTrue(course.show_calculator)

    @ddt.data('direct', 'split')
    def test_delete_item(self, default_ms):
        """
        Delete should reject on r/o db and work on r/w one
        """
        self.initdb(default_ms)
        # r/o try deleting the course
        with self.assertRaises(NotImplementedError):
            self.store.delete_item(self.xml_chapter_location)
        self.store.delete_item(self.import_chapter_location, '**replace_user**')
        # verify it's gone
        with self.assertRaises(ItemNotFoundError):
            self.store.get_instance(self.IMPORT_COURSEID, self.import_chapter_location)

    @ddt.data('direct', 'split')
    def test_get_courses(self, default_ms):
        self.initdb(default_ms)
        # we should have 3 total courses aggregated
        courses = self.store.get_courses()
        self.assertEqual(len(courses), 3)
        course_ids = [course.location for course in courses]
        self.assertIn(self.course_locations[self.IMPORT_COURSEID], course_ids)
        self.assertIn(self.course_locations[self.XML_COURSEID1], course_ids)
        self.assertIn(self.course_locations[self.XML_COURSEID2], course_ids)

    def test_xml_get_courses(self):
        """
        Test that the xml modulestore only loaded the courses from the maps.
        """
        courses = self.store.modulestores['xml'].get_courses()
        self.assertEqual(len(courses), 2)
        course_ids = [course.location.course_id for course in courses]
        self.assertIn(self.XML_COURSEID1, course_ids)
        self.assertIn(self.XML_COURSEID2, course_ids)
        # this course is in the directory from which we loaded courses but not in the map
        self.assertNotIn("edX/toy/TT_2012_Fall", course_ids)

    @ddt.data('direct', 'split')
    def test_get_course(self, default_ms):
        self.initdb(default_ms)
        for course_locn in self.course_locations.itervalues():
            if hasattr(course_locn, 'as_course_locator'):
                locn = course_locn.as_course_locator()
            else:
                locn = course_locn.course_id
            # NOTE: use get_course if you just want the course. get_items is expensive
            course = self.store.get_course(locn)
            self.assertIsNotNone(course)
            self.assertEqual(course.location, course_locn)

    # pylint: disable=E1101
    @ddt.data('direct', 'split')
    def test_get_parent_locations(self, default_ms):
        self.initdb(default_ms)
        parents = self.store.get_parent_locations(
            self.import_chapter_location,
            self.IMPORT_COURSEID
        )
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0], self.course_locations[self.IMPORT_COURSEID])

        parents = self.store.get_parent_locations(
            self.xml_chapter_location,
            self.XML_COURSEID1
        )
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0], self.course_locations[self.XML_COURSEID1])

@ddt.ddt
class TestMixedUseLocator(TestMixedModuleStore):
    """
    Tests a mixed ms which uses Locators instead of Locations
    """
    REFERENCE_TYPE = 'xmodule.modulestore.locator.CourseLocator'

    def setUp(self):
        self.options = copy.copy(self.OPTIONS)
        self.options['reference_type'] = self.REFERENCE_TYPE
        super(TestMixedUseLocator, self).setUp()

@ddt.ddt
class TestMixedMSInit(TestMixedModuleStore):
    """
    Test initializing w/o a reference_type
    """
    REFERENCE_TYPE = None
    def setUp(self):
        self.options = copy.copy(self.OPTIONS)
        del self.options['reference_type']
        super(TestMixedMSInit, self).setUp()

    @ddt.data('direct', 'split')
    def test_use_locations(self, default_ms):
        """
        Test that use_locations defaulted correctly
        """
        self.initdb(default_ms)
        self.assertEqual(self.store.reference_type, Location)
