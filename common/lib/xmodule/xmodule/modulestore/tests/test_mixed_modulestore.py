import pymongo
from uuid import uuid4
import ddt
from mock import patch, Mock
from importlib import import_module
from collections import namedtuple

from xmodule.tests import DATA_DIR
from opaque_keys.edx.locations import Location
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.exceptions import InvalidVersionError

from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xmodule.modulestore.tests.test_location_mapper import LocMapperSetupSansDjango, loc_mapper
# Mixed modulestore depends on django, so we'll manually configure some django settings
# before importing the module
from django.conf import settings
from opaque_keys.edx.locations import SlashSeparatedCourseKey
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

    MONGO_COURSEID = 'MITx/999/2013_Spring'
    XML_COURSEID1 = 'edX/toy/2012_Fall'
    XML_COURSEID2 = 'edX/simple/2012_Fall'
    BAD_COURSE_ID = 'edX/simple'

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
            BAD_COURSE_ID: 'xml',
        },
        'stores': [
            {
                'NAME': 'draft',
                'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
            {
                'NAME': 'split',
                'ENGINE': 'xmodule.modulestore.split_mongo.SplitMongoModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
            {
                'NAME': 'xml',
                'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
                'OPTIONS': {
                    'data_dir': DATA_DIR,
                    'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                }
            },
        ]
    }

    def _compareIgnoreVersion(self, loc1, loc2, msg=None):
        """
        AssertEqual replacement for CourseLocator
        """
        if loc1.version_agnostic() != loc2.version_agnostic():
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

        patcher = patch.multiple(
            'xmodule.modulestore.mixed',
            loc_mapper=Mock(return_value=LocMapperSetupSansDjango.loc_store),
            create_modulestore_instance=create_modulestore_instance,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addTypeEqualityFunc(BlockUsageLocator, '_compareIgnoreVersion')
        self.addTypeEqualityFunc(CourseLocator, '_compareIgnoreVersion')
        # define attrs which get set in initdb to quell pylint
        self.writable_chapter_location = self.store = self.fake_location = self.xml_chapter_location = None
        self.course_locations = []

        self.user_id = ModuleStoreEnum.UserID.test

    # pylint: disable=invalid-name
    def _create_course(self, default, course_key):
        """
        Create a course w/ one item in the persistence store using the given course & item location.
        """
        course = self.store.create_course(course_key.org, course_key.course, course_key.run, self.user_id)
        category = self.writable_chapter_location.category
        block_id = self.writable_chapter_location.name
        chapter = self.store.create_item(
            # don't use course_location as it may not be the repr
            course.location, category, self.user_id, location=self.writable_chapter_location, block_id=block_id
        )
        if isinstance(course.id, CourseLocator):
            self.course_locations[self.MONGO_COURSEID] = course.location.version_agnostic()
            self.writable_chapter_location = chapter.location.version_agnostic()
        else:
            self.assertEqual(course.id, course_key)
            self.assertEqual(chapter.location, self.writable_chapter_location)

        self.course = course

    def _create_block_hierarchy(self):
        """
        Creates a hierarchy of blocks for testing
        Each block is assigned as a field of the class and can be easily accessed
        """
        BlockInfo = namedtuple('BlockInfo', 'field_name, category, display_name, sub_tree')

        trees = [
            BlockInfo(
                'chapter_x', 'chapter', 'Chapter_x', [
                    BlockInfo(
                        'sequential_x1', 'sequential', 'Sequential_x1', [
                            BlockInfo(
                                'vertical_x1a', 'vertical', 'Vertical_x1a', [
                                    BlockInfo('problem_x1a_1', 'problem', 'Problem_x1a_1', []),
                                    BlockInfo('problem_x1a_2', 'problem', 'Problem_x1a_2', []),
                                    BlockInfo('problem_x1a_3', 'problem', 'Problem_x1a_3', []),
                                ]
                            )
                        ]
                    )
                ]
            ),
            BlockInfo(
                'chapter_y', 'chapter', 'Chapter_y', [
                    BlockInfo(
                        'sequential_y1', 'sequential', 'Sequential_y1', [
                            BlockInfo(
                                'vertical_y1a', 'vertical', 'Vertical_y1a', [
                                    BlockInfo('problem_y1a_1', 'problem', 'Problem_y1a_1', []),
                                    BlockInfo('problem_y1a_2', 'problem', 'Problem_y1a_2', []),
                                    BlockInfo('problem_y1a_3', 'problem', 'Problem_y1a_3', []),
                                ]
                            )
                        ]
                    )
                ]
            )
        ]

        def create_sub_tree(parent, block_info):
            block = self.store.create_item(parent.location, block_info.category, self.user_id, block_id=block_info.display_name)
            for tree in block_info.sub_tree:
                create_sub_tree(block, tree)
            # reload the block to update its children field
            block = self.store.get_item(block.location)
            setattr(self, block_info.field_name, block)

        for tree in trees:
            create_sub_tree(self.course, tree)

    def _course_key_from_string(self, string):
        """
        Get the course key for the given course string
        """
        return self.course_locations[string].course_key

    def initdb(self, default):
        """
        Initialize the database and create one test course in it
        """
        # set the default modulestore
        store_configs = self.options['stores']
        for index in range(len(store_configs)):
            if store_configs[index]['NAME'] == default:
                if index > 0:
                    store_configs[index], store_configs[0] = store_configs[0], store_configs[index]
                break
        self.store = MixedModuleStore(None, **self.options)
        self.addCleanup(self.store.close_all_connections)

        # convert to CourseKeys
        self.course_locations = {
            course_id: SlashSeparatedCourseKey.from_deprecated_string(course_id)
            for course_id in [self.MONGO_COURSEID, self.XML_COURSEID1, self.XML_COURSEID2]
        }
        # and then to the root UsageKey
        self.course_locations = {
            course_id: course_key.make_usage_key('course', course_key.run)
            for course_id, course_key in self.course_locations.iteritems()  # pylint: disable=maybe-no-member
        }
        self.fake_location = Location('foo', 'bar', 'slowly', 'vertical', 'baz')
        self.writable_chapter_location = self.course_locations[self.MONGO_COURSEID].replace(
            category='chapter', name='Overview'
        )
        self.xml_chapter_location = self.course_locations[self.XML_COURSEID1].replace(
            category='chapter', name='Overview'
        )

        # get Locators and set up the loc mapper if app is Locator based
        if default == 'split':
            self.fake_location = loc_mapper().translate_location(self.fake_location)

        self._create_course(default, self.course_locations[self.MONGO_COURSEID].course_key)

    @ddt.data('draft', 'split')
    def test_get_modulestore_type(self, default_ms):
        """
        Make sure we get back the store type we expect for given mappings
        """
        self.initdb(default_ms)
        self.assertEqual(self.store.get_modulestore_type(
            self._course_key_from_string(self.XML_COURSEID1)), ModuleStoreEnum.Type.xml
        )
        self.assertEqual(self.store.get_modulestore_type(
            self._course_key_from_string(self.XML_COURSEID2)), ModuleStoreEnum.Type.xml
        )
        mongo_ms_type = ModuleStoreEnum.Type.mongo if default_ms == 'draft' else ModuleStoreEnum.Type.split
        self.assertEqual(self.store.get_modulestore_type(
            self._course_key_from_string(self.MONGO_COURSEID)), mongo_ms_type
        )
        # try an unknown mapping, it should be the 'default' store
        self.assertEqual(self.store.get_modulestore_type(
            SlashSeparatedCourseKey('foo', 'bar', '2012_Fall')), mongo_ms_type
        )

    @ddt.data('draft', 'split')
    def test_has_item(self, default_ms):
        self.initdb(default_ms)
        for course_locn in self.course_locations.itervalues():  # pylint: disable=maybe-no-member
            self.assertTrue(self.store.has_item(course_locn))

        # try negative cases
        self.assertFalse(self.store.has_item(
            self.course_locations[self.XML_COURSEID1].replace(name='not_findable', category='problem')
        ))
        self.assertFalse(self.store.has_item(self.fake_location))

    @ddt.data('draft', 'split')
    def test_get_item(self, default_ms):
        self.initdb(default_ms)
        for course_locn in self.course_locations.itervalues():  # pylint: disable=maybe-no-member
            self.assertIsNotNone(self.store.get_item(course_locn))

        # try negative cases
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(
                self.course_locations[self.XML_COURSEID1].replace(name='not_findable', category='problem')
            )
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.fake_location)

    @ddt.data('draft', 'split')
    def test_get_items(self, default_ms):
        self.initdb(default_ms)
        for course_locn in self.course_locations.itervalues():  # pylint: disable=maybe-no-member
            locn = course_locn.course_key
            # NOTE: use get_course if you just want the course. get_items is expensive
            modules = self.store.get_items(locn, category='course')
            self.assertEqual(len(modules), 1)
            self.assertEqual(modules[0].location, course_locn)

    @ddt.data('draft', 'split')
    def test_update_item(self, default_ms):
        """
        Update should fail for r/o dbs and succeed for r/w ones
        """
        self.initdb(default_ms)
        course = self.store.get_course(self.course_locations[self.XML_COURSEID1].course_key)
        # if following raised, then the test is really a noop, change it
        self.assertFalse(course.show_calculator, "Default changed making test meaningless")
        course.show_calculator = True
        with self.assertRaises(NotImplementedError):  # ensure it doesn't allow writing
            self.store.update_item(course, self.user_id)
        # now do it for a r/w db
        course = self.store.get_course(self.course_locations[self.MONGO_COURSEID].course_key)
        # if following raised, then the test is really a noop, change it
        self.assertFalse(course.show_calculator, "Default changed making test meaningless")
        course.show_calculator = True
        self.store.update_item(course, self.user_id)
        course = self.store.get_course(self.course_locations[self.MONGO_COURSEID].course_key)
        self.assertTrue(course.show_calculator)

    @ddt.data('draft', 'split')
    def test_delete_item(self, default_ms):
        """
        Delete should reject on r/o db and work on r/w one
        """
        self.initdb(default_ms)
        # r/o try deleting the course (is here to ensure it can't be deleted)
        with self.assertRaises(NotImplementedError):
            self.store.delete_item(self.xml_chapter_location, self.user_id)
        self.store.delete_item(self.writable_chapter_location, self.user_id)
        # verify it's gone
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.writable_chapter_location)

    @ddt.data('draft', 'split')
    def test_get_courses(self, default_ms):
        self.initdb(default_ms)
        # we should have 3 total courses across all stores
        courses = self.store.get_courses()
        course_ids = [
            course.location.version_agnostic()
            if hasattr(course.location, 'version_agnostic') else course.location
            for course in courses
        ]
        self.assertEqual(len(courses), 3, "Not 3 courses: {}".format(course_ids))
        self.assertIn(self.course_locations[self.MONGO_COURSEID], course_ids)
        self.assertIn(self.course_locations[self.XML_COURSEID1], course_ids)
        self.assertIn(self.course_locations[self.XML_COURSEID2], course_ids)

    def test_xml_get_courses(self):
        """
        Test that the xml modulestore only loaded the courses from the maps.
        """
        self.initdb('draft')
        xml_store = self.store._get_modulestore_by_type(ModuleStoreEnum.Type.xml)
        courses = xml_store.get_courses()
        self.assertEqual(len(courses), 2)
        course_ids = [course.id for course in courses]
        self.assertIn(self.course_locations[self.XML_COURSEID1].course_key, course_ids)
        self.assertIn(self.course_locations[self.XML_COURSEID2].course_key, course_ids)
        # this course is in the directory from which we loaded courses but not in the map
        self.assertNotIn("edX/toy/TT_2012_Fall", course_ids)

    def test_xml_no_write(self):
        """
        Test that the xml modulestore doesn't allow write ops.
        """
        self.initdb('draft')
        xml_store = self.store._get_modulestore_by_type(ModuleStoreEnum.Type.xml)
        # the important thing is not which exception it raises but that it raises an exception
        with self.assertRaises(AttributeError):
<<<<<<< HEAD
            xml_store.create_course("org", "course/run", self.user_id)
=======
            xml_store.create_course("org", "course", "run", 999)
>>>>>>> Fix up the signature to use course and run instead of just offering

    @ddt.data('draft', 'split')
    def test_get_course(self, default_ms):
        self.initdb(default_ms)
        for course_location in self.course_locations.itervalues():  # pylint: disable=maybe-no-member
            # NOTE: use get_course if you just want the course. get_items is expensive
            course = self.store.get_course(course_location.course_key)
            self.assertIsNotNone(course)
            self.assertEqual(course.id, course_location.course_key)

    @ddt.data('draft', 'split')
    def test_get_parent_locations(self, default_ms):
        self.initdb(default_ms)
        parent = self.store.get_parent_location(self.writable_chapter_location)
        self.assertEqual(parent, self.course_locations[self.MONGO_COURSEID])

        parent = self.store.get_parent_location(self.xml_chapter_location)
        self.assertEqual(parent, self.course_locations[self.XML_COURSEID1])

    def verify_get_parent_locations_results(self, expected_results):
        # expected_results should be a list of (child, parent, revision)
        for test in expected_results:
            self.assertEqual(
                test[1].location if test[1] else None,
                self.store.get_parent_location(test[0].location, revision=test[2])
            )

    @ddt.data('draft')
    def test_get_parent_locations_moved_child(self, default_ms):
        self.initdb(default_ms)
        self._create_block_hierarchy()

        # publish the course
        self.store.publish(self.course.location, self.user_id)

        # make drafts of verticals
        self.store.convert_to_draft(self.vertical_x1a.location, self.user_id)
        self.store.convert_to_draft(self.vertical_y1a.location, self.user_id)

        # move child problem_x1a_1 to vertical_y1a
        child_to_move = self.problem_x1a_1
        old_parent = self.vertical_x1a
        new_parent = self.vertical_y1a
        old_parent.children.remove(child_to_move.location)
        new_parent.children.append(child_to_move.location)
        self.store.update_item(old_parent, self.user_id)
        self.store.update_item(new_parent, self.user_id)

        self.verify_get_parent_locations_results([
            (child_to_move, new_parent, None),
            (child_to_move, new_parent, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_move, old_parent, ModuleStoreEnum.RevisionOption.published_only),
        ])

        # publish the course again
        self.store.publish(self.course.location, self.user_id)
        self.verify_get_parent_locations_results([
            (child_to_move, new_parent, None),
            (child_to_move, new_parent, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_move, new_parent, ModuleStoreEnum.RevisionOption.published_only),
        ])

    @ddt.data('draft')
    def test_get_parent_locations_deleted_child(self, default_ms):
        self.initdb(default_ms)
        self._create_block_hierarchy()

        # publish the course
        self.store.publish(self.course.location, self.user_id)

        # make draft of vertical
        self.store.convert_to_draft(self.vertical_y1a.location, self.user_id)

        # delete child problem_y1a_1
        child_to_delete = self.problem_y1a_1
        old_parent = self.vertical_y1a
        self.store.delete_item(child_to_delete.location, self.user_id)

        self.verify_get_parent_locations_results([
            (child_to_delete, old_parent, None),
            # Note: The following could be an unexpected result, but we want to avoid an extra database call
            (child_to_delete, old_parent, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_delete, old_parent, ModuleStoreEnum.RevisionOption.published_only),
        ])

        # publish the course again
        self.store.publish(self.course.location, self.user_id)
        self.verify_get_parent_locations_results([
            (child_to_delete, None, None),
            (child_to_delete, None, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_delete, None, ModuleStoreEnum.RevisionOption.published_only),
        ])


    @ddt.data('draft')
    def test_revert_to_published_root_draft(self, default_ms):
        """
        Test calling revert_to_published on draft vertical.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.publish(self.course.location, self.user_id)

        # delete leaf problem (will make parent vertical a draft)
        self.store.delete_item(self.problem_x1a_1.location, self.user_id)

        draft_parent = self.store.get_item(self.vertical_x1a.location)
        self.assertEqual(2, len(draft_parent.children))
        published_parent = self.store.get_item(
            self.vertical_x1a.location,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self.assertEqual(3, len(published_parent.children))

        self.store.revert_to_published(self.vertical_x1a.location, self.user_id)
        reverted_parent = self.store.get_item(self.vertical_x1a.location)
        self.assertEqual(3, len(published_parent.children))
        self.assertEqual(reverted_parent, published_parent)

    @ddt.data('draft')
    def test_revert_to_published_root_published(self, default_ms):
        """
        Test calling revert_to_published on a published vertical with a draft child.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.publish(self.course.location, self.user_id)

        orig_display_name = self.problem_x1a_1.display_name

        # Change display name of problem and update just it (so parent remains published)
        self.problem_x1a_1.display_name = "updated before calling revert"
        self.store.update_item(self.problem_x1a_1, self.user_id)
        self.store.revert_to_published(self.vertical_x1a.location, self.user_id)

        reverted_problem = self.store.get_item(self.problem_x1a_1.location)
        self.assertEqual(orig_display_name, reverted_problem.display_name)

    @ddt.data('draft')
    def test_revert_to_published_no_draft(self, default_ms):
        """
        Test calling revert_to_published on vertical with no draft content does nothing.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.publish(self.course.location, self.user_id)

        orig_vertical = self.vertical_x1a
        self.store.revert_to_published(self.vertical_x1a.location, self.user_id)
        reverted_vertical = self.store.get_item(self.vertical_x1a.location)
        self.assertEqual(orig_vertical, reverted_vertical)

    @ddt.data('draft')
    def test_revert_to_published_no_published(self, default_ms):
        """
        Test calling revert_to_published on vertical with no published version errors.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        with self.assertRaises(InvalidVersionError):
            self.store.revert_to_published(self.vertical_x1a.location)

    @ddt.data('draft')
    def test_revert_to_published_direct_only(self, default_ms):
        """
        Test calling revert_to_published on a direct-only item is a no-op.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.revert_to_published(self.sequential_x1.location)
        reverted_parent = self.store.get_item(self.sequential_x1.location)
        # It does not discard the child vertical, even though that child is a draft (with no published version)
        self.assertEqual(1, len(reverted_parent.children))

    @ddt.data('draft', 'split')
    def test_get_orphans(self, default_ms):
        self.initdb(default_ms)
        # create an orphan
        course_id = self.course_locations[self.MONGO_COURSEID].course_key
        orphan = self.store.create_item(course_id, 'problem', self.user_id, block_id='orphan')
        found_orphans = self.store.get_orphans(self.course_locations[self.MONGO_COURSEID].course_key)
        if default_ms == 'split':
            self.assertEqual(found_orphans, [orphan.location.version_agnostic()])
        else:
            self.assertEqual(found_orphans, [orphan.location.to_deprecated_string()])

    @ddt.data('draft')
    def test_create_item_from_parent_location(self, default_ms):
        """
        Test a code path missed by the above: passing an old-style location as parent but no
        new location for the child
        """
        self.initdb(default_ms)
        self.store.create_item(self.course_locations[self.MONGO_COURSEID], 'problem', self.user_id, block_id='orphan')
        orphans = self.store.get_orphans(self.course_locations[self.MONGO_COURSEID].course_key)
        self.assertEqual(len(orphans), 0, "unexpected orphans: {}".format(orphans))

    @ddt.data('draft')
    def test_get_courses_for_wiki(self, default_ms):
        """
        Test the get_courses_for_wiki method
        """
        self.initdb(default_ms)
        course_locations = self.store.get_courses_for_wiki('toy')
        self.assertEqual(len(course_locations), 1)
        self.assertIn(self.course_locations[self.XML_COURSEID1], course_locations)

        course_locations = self.store.get_courses_for_wiki('simple')
        self.assertEqual(len(course_locations), 1)
        self.assertIn(self.course_locations[self.XML_COURSEID2], course_locations)

        self.assertEqual(len(self.store.get_courses_for_wiki('edX.simple.2012_Fall')), 0)
        self.assertEqual(len(self.store.get_courses_for_wiki('no_such_wiki')), 0)


#=============================================================================================================
# General utils for not using django settings
#=============================================================================================================


def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


# pylint: disable=unused-argument
def create_modulestore_instance(engine, contentstore, doc_store_config, options, i18n_service=None):
    """
    This will return a new instance of a modulestore given an engine and options
    """
    class_ = load_function(engine)

    return class_(
        doc_store_config=doc_store_config,
        contentstore=contentstore,
        branch_setting_func=lambda: ModuleStoreEnum.Branch.draft_preferred,
        **options
    )
