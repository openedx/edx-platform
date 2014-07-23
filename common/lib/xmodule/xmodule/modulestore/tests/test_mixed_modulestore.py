import pymongo
from uuid import uuid4
import ddt
from mock import patch
from importlib import import_module
from collections import namedtuple
import unittest
import datetime
from pytz import UTC

from xmodule.tests import DATA_DIR
from opaque_keys.edx.locations import Location
from xmodule.modulestore import ModuleStoreEnum, PublishState
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.exceptions import InvalidVersionError

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
# Mixed modulestore depends on django, so we'll manually configure some django settings
# before importing the module
# TODO remove this import and the configuration -- xmodule should not depend on django!
from django.conf import settings
if not settings.configured:
    settings.configure()
from xmodule.modulestore.mixed import MixedModuleStore


@ddt.ddt
class TestMixedModuleStore(unittest.TestCase):
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
                'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
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
        # create course
        self.course = self.store.create_course(course_key.org, course_key.course, course_key.run, self.user_id)
        if isinstance(self.course.id, CourseLocator):
            self.course_locations[self.MONGO_COURSEID] = self.course.location.version_agnostic()
        else:
            self.assertEqual(self.course.id, course_key)

        # create chapter
        chapter = self.store.create_child(self.user_id, self.course.location, 'chapter', block_id='Overview')
        self.writable_chapter_location = chapter.location.version_agnostic()

    def _create_block_hierarchy(self):
        """
        Creates a hierarchy of blocks for testing
        Each block's (version_agnostic) location is assigned as a field of the class and can be easily accessed
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
                                    BlockInfo('html_x1a_1', 'html', 'HTML_x1a_1', []),
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
            block = self.store.create_child(
                self.user_id, parent.location.version_agnostic(),
                block_info.category, block_id=block_info.display_name
            )
            for tree in block_info.sub_tree:
                create_sub_tree(block, tree)
            setattr(self, block_info.field_name, block.location.version_agnostic())

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
        self.store = MixedModuleStore(None, create_modulestore_instance=create_modulestore_instance, **self.options)
        self.addCleanup(self.store.close_all_connections)

        # convert to CourseKeys
        self.course_locations = {
            course_id: CourseLocator.from_string(course_id)
            for course_id in [self.MONGO_COURSEID, self.XML_COURSEID1, self.XML_COURSEID2]
        }
        # and then to the root UsageKey
        self.course_locations = {
            course_id: course_key.make_usage_key('course', course_key.run)
            for course_id, course_key in self.course_locations.iteritems()  # pylint: disable=maybe-no-member
        }
        if default == 'split':
            self.fake_location = CourseLocator(
                'foo', 'bar', 'slowly', branch=ModuleStoreEnum.BranchName.draft
            ).make_usage_key('vertical', 'baz')
        else:
            self.fake_location = Location('foo', 'bar', 'slowly', 'vertical', 'baz')
        self.xml_chapter_location = self.course_locations[self.XML_COURSEID1].replace(
            category='chapter', name='Overview'
        )
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
        # r/o try deleting the chapter (is here to ensure it can't be deleted)
        with self.assertRaises(NotImplementedError):
            self.store.delete_item(self.xml_chapter_location, self.user_id)
        self.store.delete_item(self.writable_chapter_location, self.user_id)
        # verify it's gone
        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.writable_chapter_location)

        # create and delete a private vertical with private children
        private_vert = self.store.create_child(
            # don't use course_location as it may not be the repr
            self.user_id, self.course_locations[self.MONGO_COURSEID],
            'vertical', block_id='private'
        )
        private_leaf = self.store.create_child(
            # don't use course_location as it may not be the repr
            self.user_id, private_vert.location, 'html', block_id='private_leaf'
        )

        # verify pre delete state (just to verify that the test is valid)
        self.assertTrue(hasattr(private_vert, 'is_draft') or private_vert.location.branch == ModuleStoreEnum.BranchName.draft)
        if hasattr(private_vert.location, 'version_guid'):
            # change to the HEAD version
            vert_loc = private_vert.location.for_version(private_leaf.location.version_guid)
        else:
            vert_loc = private_vert.location
        self.assertTrue(self.store.has_item(vert_loc))
        self.assertTrue(self.store.has_item(private_leaf.location))
        course = self.store.get_course(self.course_locations[self.MONGO_COURSEID].course_key, 0)
        self.assertIn(vert_loc, course.children)

        # update the component to force it to draft w/o forcing the unit to draft
        # delete the vertical and ensure the course no longer points to it
        self.store.delete_item(vert_loc, self.user_id)
        course = self.store.get_course(self.course_locations[self.MONGO_COURSEID].course_key, 0)
        if hasattr(private_vert.location, 'version_guid'):
            # change to the HEAD version
            vert_loc = private_vert.location.for_version(course.location.version_guid)
            leaf_loc = private_leaf.location.for_version(course.location.version_guid)
        else:
            vert_loc = private_vert.location
            leaf_loc = private_leaf.location
        self.assertFalse(self.store.has_item(vert_loc))
        self.assertFalse(self.store.has_item(leaf_loc))
        self.assertNotIn(vert_loc, course.children)

        # TODO can remove this once LMS-2869 is implemented
        # first create a Published branch
        self.store.publish(self.course_locations[self.MONGO_COURSEID], self.user_id)

        # reproduce bug STUD-1965
        # create and delete a private vertical with private children
        private_vert = self.store.create_child(
            # don't use course_location as it may not be the repr
             self.user_id, self.course_locations[self.MONGO_COURSEID], 'vertical', block_id='publish'
        )
        private_leaf = self.store.create_child(
            self.user_id, private_vert.location, 'html', block_id='bug_leaf'
        )

        self.store.publish(private_vert.location, self.user_id)
        private_leaf.display_name = 'change me'
        private_leaf = self.store.update_item(private_leaf, self.user_id)
        # test succeeds if delete succeeds w/o error
        self.store.delete_item(private_leaf.location, self.user_id)

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

    @ddt.data('draft')
    def test_has_changes_draft_mongo(self, default_ms):
        """
        Smoke test for has_changes with draft mongo modulestore.

        Tests already exist for both split and draft in their own test files.
        """
        self.initdb(default_ms)
        item = self.store.create_item(
            self.user_id, self.course_locations[self.MONGO_COURSEID].course_key, 'problem', block_id='orphan'
        )
        self.assertTrue(self.store.has_changes(item.location))
        self.store.publish(item.location, self.user_id)
        self.assertFalse(self.store.has_changes(item.location))

    @ddt.data('split')
    def test_has_changes_split(self, default_ms):
        """
        Smoke test for has_changes with split modulestore.

        Tests already exist for both split and draft in their own test files.
        """
        self.initdb(default_ms)
        self.assertTrue(self.store.has_changes(self.writable_chapter_location))
        # split modulestore's "publish" method is currently called "xblock_publish"

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
            xml_store.create_course("org", "course", "run", self.user_id)

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
        for child_location, parent_location, revision in expected_results:
            self.assertEqual(
                parent_location,
                self.store.get_parent_location(child_location, revision=revision)
            )

    @ddt.data('draft', 'split')
    def test_get_parent_locations_moved_child(self, default_ms):
        self.initdb(default_ms)
        self._create_block_hierarchy()

        # publish the course
        self.store.publish(self.course.location, self.user_id)

        # make drafts of verticals
        self.store.convert_to_draft(self.vertical_x1a, self.user_id)
        self.store.convert_to_draft(self.vertical_y1a, self.user_id)

        # move child problem_x1a_1 to vertical_y1a
        child_to_move_location = self.problem_x1a_1
        new_parent_location = self.vertical_y1a
        old_parent_location = self.vertical_x1a

        old_parent = self.store.get_item(old_parent_location)
        old_parent.children.remove(child_to_move_location.replace(version_guid=old_parent.location.version_guid))
        self.store.update_item(old_parent, self.user_id)

        new_parent = self.store.get_item(new_parent_location)
        new_parent.children.append(child_to_move_location.replace(version_guid=new_parent.location.version_guid))
        self.store.update_item(new_parent, self.user_id)

        self.verify_get_parent_locations_results([
            (child_to_move_location, new_parent_location, None),
            (child_to_move_location, new_parent_location, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_move_location, old_parent_location.for_branch(ModuleStoreEnum.BranchName.published), ModuleStoreEnum.RevisionOption.published_only),
        ])

        # publish the course again
        self.store.publish(self.course.location, self.user_id)
        self.verify_get_parent_locations_results([
            (child_to_move_location, new_parent_location, None),
            (child_to_move_location, new_parent_location, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_move_location, new_parent_location.for_branch(ModuleStoreEnum.BranchName.published), ModuleStoreEnum.RevisionOption.published_only),
        ])

    @ddt.data('draft')
    def test_get_parent_locations_deleted_child(self, default_ms):
        self.initdb(default_ms)
        self._create_block_hierarchy()

        # publish the course
        self.store.publish(self.course.location, self.user_id)

        # make draft of vertical
        self.store.convert_to_draft(self.vertical_y1a, self.user_id)

        # delete child problem_y1a_1
        child_to_delete_location = self.problem_y1a_1
        old_parent_location = self.vertical_y1a
        self.store.delete_item(child_to_delete_location, self.user_id)

        self.verify_get_parent_locations_results([
            (child_to_delete_location, old_parent_location, None),
            # Note: The following could be an unexpected result, but we want to avoid an extra database call
            (child_to_delete_location, old_parent_location, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_delete_location, old_parent_location, ModuleStoreEnum.RevisionOption.published_only),
        ])

        # publish the course again
        self.store.publish(self.course.location, self.user_id)
        self.verify_get_parent_locations_results([
            (child_to_delete_location, None, None),
            (child_to_delete_location, None, ModuleStoreEnum.RevisionOption.draft_preferred),
            (child_to_delete_location, None, ModuleStoreEnum.RevisionOption.published_only),
        ])

    @ddt.data('draft')
    def test_revert_to_published_root_draft(self, default_ms):
        """
        Test calling revert_to_published on draft vertical.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()

        vertical = self.store.get_item(self.vertical_x1a)
        vertical_children_num = len(vertical.children)

        self.store.publish(self.course.location, self.user_id)

        # delete leaf problem (will make parent vertical a draft)
        self.store.delete_item(self.problem_x1a_1, self.user_id)

        draft_parent = self.store.get_item(self.vertical_x1a)
        self.assertEqual(vertical_children_num - 1, len(draft_parent.children))
        published_parent = self.store.get_item(
            self.vertical_x1a,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self.assertEqual(vertical_children_num, len(published_parent.children))

        self.store.revert_to_published(self.vertical_x1a, self.user_id)
        reverted_parent = self.store.get_item(self.vertical_x1a)
        self.assertEqual(vertical_children_num, len(published_parent.children))
        self.assertEqual(reverted_parent, published_parent)

    @ddt.data('draft')
    def test_revert_to_published_root_published(self, default_ms):
        """
        Test calling revert_to_published on a published vertical with a draft child.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.publish(self.course.location, self.user_id)

        problem = self.store.get_item(self.problem_x1a_1)
        orig_display_name = problem.display_name

        # Change display name of problem and update just it (so parent remains published)
        problem.display_name = "updated before calling revert"
        self.store.update_item(problem, self.user_id)
        self.store.revert_to_published(self.vertical_x1a, self.user_id)

        reverted_problem = self.store.get_item(self.problem_x1a_1)
        self.assertEqual(orig_display_name, reverted_problem.display_name)

    @ddt.data('draft')
    def test_revert_to_published_no_draft(self, default_ms):
        """
        Test calling revert_to_published on vertical with no draft content does nothing.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.publish(self.course.location, self.user_id)

        orig_vertical = self.store.get_item(self.vertical_x1a)
        self.store.revert_to_published(self.vertical_x1a, self.user_id)
        reverted_vertical = self.store.get_item(self.vertical_x1a)
        self.assertEqual(orig_vertical, reverted_vertical)

    @ddt.data('draft')
    def test_revert_to_published_no_published(self, default_ms):
        """
        Test calling revert_to_published on vertical with no published version errors.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        with self.assertRaises(InvalidVersionError):
            self.store.revert_to_published(self.vertical_x1a, self.user_id)

    @ddt.data('draft')
    def test_revert_to_published_direct_only(self, default_ms):
        """
        Test calling revert_to_published on a direct-only item is a no-op.
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()
        self.store.revert_to_published(self.sequential_x1, self.user_id)
        reverted_parent = self.store.get_item(self.sequential_x1)
        # It does not discard the child vertical, even though that child is a draft (with no published version)
        self.assertEqual(1, len(reverted_parent.children))

    @ddt.data('draft', 'split')
    def test_get_orphans(self, default_ms):
        self.initdb(default_ms)
        course_id = self.course_locations[self.MONGO_COURSEID].course_key

        # create parented children
        self._create_block_hierarchy()

        # orphans
        orphan_locations = [
            course_id.make_usage_key('chapter', 'OrphanChapter'),
            course_id.make_usage_key('vertical', 'OrphanVertical'),
            course_id.make_usage_key('problem', 'OrphanProblem'),
            course_id.make_usage_key('html', 'OrphanHTML'),
        ]

        # detached items (not considered as orphans)
        detached_locations = [
            course_id.make_usage_key('static_tab', 'StaticTab'),
            course_id.make_usage_key('about', 'overview'),
            course_id.make_usage_key('course_info', 'updates'),
        ]

        for location in (orphan_locations + detached_locations):
            self.store.create_item(
                self.user_id,
                location.course_key,
                location.block_type,
                block_id=location.block_id
            )

        found_orphans = self.store.get_orphans(self.course_locations[self.MONGO_COURSEID].course_key)
        self.assertEqual(set(found_orphans), set(orphan_locations))

    @ddt.data('draft')
    def test_create_item_from_parent_location(self, default_ms):
        """
        Test a code path missed by the above: passing an old-style location as parent but no
        new location for the child
        """
        self.initdb(default_ms)
        self.store.create_child(
            self.user_id,
            self.course_locations[self.MONGO_COURSEID],
            'problem',
            block_id='orphan'
        )
        orphans = self.store.get_orphans(self.course_locations[self.MONGO_COURSEID].course_key)
        self.assertEqual(len(orphans), 0, "unexpected orphans: {}".format(orphans))

    @ddt.data('draft', 'split')
    def test_create_item_populates_edited_info(self, default_ms):
        self.initdb(default_ms)
        block = self.store.create_item(
            self.user_id,
            self.course.location.version_agnostic().course_key,
            'problem'
        )
        self.assertEqual(self.user_id, block.edited_by)
        self.assertGreater(datetime.datetime.now(UTC), block.edited_on)

    @ddt.data('draft')
    def test_create_item_populates_subtree_edited_info(self, default_ms):
        self.initdb(default_ms)
        block = self.store.create_item(
            self.user_id,
            self.course.location.version_agnostic().course_key,
            'problem'
        )
        self.assertEqual(self.user_id, block.subtree_edited_by)
        self.assertGreater(datetime.datetime.now(UTC), block.subtree_edited_on)

    @ddt.data('draft', 'split')
    def test_get_courses_for_wiki(self, default_ms):
        """
        Test the get_courses_for_wiki method
        """
        self.initdb(default_ms)
        # Test XML wikis
        wiki_courses = self.store.get_courses_for_wiki('toy')
        self.assertEqual(len(wiki_courses), 1)
        self.assertIn(self.course_locations[self.XML_COURSEID1].course_key, wiki_courses)

        wiki_courses = self.store.get_courses_for_wiki('simple')
        self.assertEqual(len(wiki_courses), 1)
        self.assertIn(self.course_locations[self.XML_COURSEID2].course_key, wiki_courses)

        # Test Mongo wiki
        wiki_courses = self.store.get_courses_for_wiki('999')
        self.assertEqual(len(wiki_courses), 1)
        self.assertIn(
            self.course_locations[self.MONGO_COURSEID].course_key.replace(branch=None),  # Branch agnostic
            wiki_courses
        )

        self.assertEqual(len(self.store.get_courses_for_wiki('edX.simple.2012_Fall')), 0)
        self.assertEqual(len(self.store.get_courses_for_wiki('no_such_wiki')), 0)

    @ddt.data('draft', 'split')
    def test_unpublish(self, default_ms):
        """
        Test calling unpublish
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()

        # publish
        self.store.publish(self.course.location, self.user_id)
        published_xblock = self.store.get_item(
            self.vertical_x1a,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self.assertIsNotNone(published_xblock)

        # unpublish
        self.store.unpublish(self.vertical_x1a, self.user_id)

        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(
                self.vertical_x1a,
                revision=ModuleStoreEnum.RevisionOption.published_only
            )

        # make sure draft version still exists
        draft_xblock = self.store.get_item(
            self.vertical_x1a,
            revision=ModuleStoreEnum.RevisionOption.draft_only
        )
        self.assertIsNotNone(draft_xblock)

    @ddt.data('draft', 'split')
    def test_compute_publish_state(self, default_ms):
        """
        Test the compute_publish_state method
        """
        self.initdb(default_ms)
        self._create_block_hierarchy()

        # TODO - Remove this call to explicitly Publish the course once LMS-2869 is implemented
        # For now, we need this since we can't publish a child item without its course already been published
        course_location = self.course_locations[self.MONGO_COURSEID]
        self.store.publish(course_location, self.user_id)

        # start off as Private
        item = self.store.create_child(self.user_id, self.writable_chapter_location, 'problem', 'test_compute_publish_state')
        item_location = item.location.version_agnostic()
        self.assertEquals(self.store.compute_publish_state(item), PublishState.private)

        # Private -> Public
        self.store.publish(item_location, self.user_id)
        item = self.store.get_item(item_location)
        self.assertEquals(self.store.compute_publish_state(item), PublishState.public)

        # Public -> Private
        self.store.unpublish(item_location, self.user_id)
        item = self.store.get_item(item_location)
        self.assertEquals(self.store.compute_publish_state(item), PublishState.private)

        # Private -> Public
        self.store.publish(item_location, self.user_id)
        item = self.store.get_item(item_location)
        self.assertEquals(self.store.compute_publish_state(item), PublishState.public)

        # Public -> Draft with NO changes
        # Note: This is where Split and Mongo differ
        self.store.convert_to_draft(item_location, self.user_id)
        item = self.store.get_item(item_location)
        self.assertEquals(
            self.store.compute_publish_state(item),
            PublishState.draft if default_ms == 'draft' else PublishState.public
        )

        # Draft WITH changes
        item.display_name = 'new name'
        item = self.store.update_item(item, self.user_id)
        self.assertTrue(self.store.has_changes(item.location))
        self.assertEquals(self.store.compute_publish_state(item), PublishState.draft)

    @ddt.data('draft', 'split')
    def test_get_courses_for_wiki_shared(self, default_ms):
        """
        Test two courses sharing the same wiki
        """
        self.initdb(default_ms)

        # verify initial state - initially, we should have a wiki for the Mongo course
        wiki_courses = self.store.get_courses_for_wiki('999')
        self.assertIn(
            self.course_locations[self.MONGO_COURSEID].course_key.replace(branch=None),  # Branch agnostic
            wiki_courses
        )

        # set Mongo course to share the wiki with simple course
        mongo_course = self.store.get_course(self.course_locations[self.MONGO_COURSEID].course_key)
        mongo_course.wiki_slug = 'simple'
        self.store.update_item(mongo_course, self.user_id)

        # now mongo_course should not be retrievable with old wiki_slug
        wiki_courses = self.store.get_courses_for_wiki('999')
        self.assertEqual(len(wiki_courses), 0)

        # but there should be two courses with wiki_slug 'simple'
        wiki_courses = self.store.get_courses_for_wiki('simple')
        self.assertEqual(len(wiki_courses), 2)
        self.assertIn(
            self.course_locations[self.MONGO_COURSEID].course_key.replace(branch=None),
            wiki_courses
        )
        self.assertIn(self.course_locations[self.XML_COURSEID2].course_key, wiki_courses)

        # configure mongo course to use unique wiki_slug.
        mongo_course = self.store.get_course(self.course_locations[self.MONGO_COURSEID].course_key)
        mongo_course.wiki_slug = 'MITx.999.2013_Spring'
        self.store.update_item(mongo_course, self.user_id)
        # it should be retrievable with its new wiki_slug
        wiki_courses = self.store.get_courses_for_wiki('MITx.999.2013_Spring')
        self.assertEqual(len(wiki_courses), 1)
        self.assertIn(
            self.course_locations[self.MONGO_COURSEID].course_key.replace(branch=None),
            wiki_courses
        )
        # and NOT retriveable with its old wiki_slug
        wiki_courses = self.store.get_courses_for_wiki('simple')
        self.assertEqual(len(wiki_courses), 1)
        self.assertNotIn(
            self.course_locations[self.MONGO_COURSEID].course_key.replace(branch=None),
            wiki_courses
        )
        self.assertIn(
            self.course_locations[self.XML_COURSEID2].course_key,
            wiki_courses
        )


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
