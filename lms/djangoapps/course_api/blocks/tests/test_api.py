"""
Tests for Blocks api.py
"""

from django.test.client import RequestFactory

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.block_structure.api import update_course_in_cache
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory

from ..api import get_blocks


class TestGetBlocks(SharedModuleStoreTestCase):
    """
    Tests for the get_blocks function
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetBlocks, cls).setUpClass()
        cls.course = SampleCourseFactory.create()

        # hide the html block
        cls.html_block = cls.store.get_item(cls.course.id.make_usage_key('html', 'html_x1a_1'))
        cls.html_block.visible_to_staff_only = True
        cls.store.update_item(cls.html_block, ModuleStoreEnum.UserID.test)

    def setUp(self):
        super(TestGetBlocks, self).setUp()
        self.user = UserFactory.create()
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user

    def test_basic(self):
        blocks = get_blocks(self.request, self.course.location, self.user)
        self.assertEquals(blocks['root'], unicode(self.course.location))

        # subtract for (1) the orphaned course About block and (2) the hidden Html block
        self.assertEquals(len(blocks['blocks']), len(self.store.get_items(self.course.id)) - 2)
        self.assertNotIn(unicode(self.html_block.location), blocks['blocks'])

    def test_no_user(self):
        blocks = get_blocks(self.request, self.course.location)
        self.assertIn(unicode(self.html_block.location), blocks['blocks'])

    def test_access_before_api_transformer_order(self):
        """
        Tests the order of transformers: access checks are made before the api
        transformer is applied.
        """
        blocks = get_blocks(self.request, self.course.location, self.user, nav_depth=5, requested_fields=['nav_depth'])
        vertical_block = self.store.get_item(self.course.id.make_usage_key('vertical', 'vertical_x1a'))
        problem_block = self.store.get_item(self.course.id.make_usage_key('problem', 'problem_x1a_1'))

        vertical_descendants = blocks['blocks'][unicode(vertical_block.location)]['descendants']

        self.assertIn(unicode(problem_block.location), vertical_descendants)
        self.assertNotIn(unicode(self.html_block.location), vertical_descendants)

    def test_sub_structure(self):
        sequential_block = self.store.get_item(self.course.id.make_usage_key('sequential', 'sequential_y1'))

        blocks = get_blocks(self.request, sequential_block.location, self.user)
        self.assertEquals(blocks['root'], unicode(sequential_block.location))
        self.assertEquals(len(blocks['blocks']), 5)

        for block_type, block_name, is_inside_of_structure in (
                ('vertical', 'vertical_y1a', True),
                ('problem', 'problem_y1a_1', True),
                ('chapter', 'chapter_y', False),
                ('sequential', 'sequential_x1', False),
        ):
            block = self.store.get_item(self.course.id.make_usage_key(block_type, block_name))
            if is_inside_of_structure:
                self.assertIn(unicode(block.location), blocks['blocks'])
            else:
                self.assertNotIn(unicode(block.location), blocks['blocks'])

    def test_filtering_by_block_types(self):
        sequential_block = self.store.get_item(self.course.id.make_usage_key('sequential', 'sequential_y1'))

        # not filtered blocks
        blocks = get_blocks(self.request, sequential_block.location, self.user, requested_fields=['type'])
        self.assertEquals(len(blocks['blocks']), 5)
        found_not_problem = False
        for block in blocks['blocks'].itervalues():
            if block['type'] != 'problem':
                found_not_problem = True
        self.assertTrue(found_not_problem)

        # filtered blocks
        blocks = get_blocks(self.request, sequential_block.location, self.user,
                            block_types_filter=['problem'], requested_fields=['type'])
        self.assertEquals(len(blocks['blocks']), 3)
        for block in blocks['blocks'].itervalues():
            self.assertEqual(block['type'], 'problem')

    def test_get_blocks_old_mongo_course_with_split_usage_key(self):
        """
        Test that get_blocks of old_mongo course will fetch the blocks with split_course version of usage_key.
        """
        # default test course is old_mongo making a new usage_key of split version.
        course_key = CourseKey.from_string('course-v1:org.0+course_0+Run_0')
        split_usage_key = modulestore().make_course_usage_key(course_key)

        blocks = get_blocks(self.request, split_usage_key, self.user)
        self.assertEquals(blocks['root'], unicode(self.course.location))

    def test_get_blocks_split_course_with_old_mongo_usage_key(self):
        """
        Test that get_blocks of split course will fetch the blocks with old_mongo version of usage_key.
        """
        # making split course and new usage_key of old_mongo version.
        self.course = SampleCourseFactory.create(default_store=ModuleStoreEnum.Type.split,
                                                 org='test_org',
                                                 run='test_run',
                                                 course='test_course')
        update_course_in_cache(self.course.id)  # updating the cache as get_blocks get the blocks from this.

        course_key = CourseKey.from_string('test_org/test_course/test_run')
        old_mongo_usage_key = modulestore().make_course_usage_key(course_key)

        with self.assertRaises(ItemNotFoundError):
            get_blocks(self.request, old_mongo_usage_key, self.user)
