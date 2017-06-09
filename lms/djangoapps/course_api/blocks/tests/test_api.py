"""
Tests for Blocks api.py
"""

import ddt
from django.test.client import RequestFactory

from openedx.core.djangoapps.content.block_structure.api import clear_course_from_cache
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory, check_mongo_calls

from ..api import get_blocks


class TestGetBlocks(SharedModuleStoreTestCase):
    """
    Tests for the get_blocks function
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetBlocks, cls).setUpClass()
        with cls.store.default_store(ModuleStoreEnum.Type.split):
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


@ddt.ddt
class TestGetBlocksQueryCounts(SharedModuleStoreTestCase):
    """
    Tests query counts for the get_blocks function.
    """
    def setUp(self):
        super(TestGetBlocksQueryCounts, self).setUp()

        self.user = UserFactory.create()
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user

    def _create_course(self, store_type):
        """
        Creates the sample course in the given store type.
        """
        with self.store.default_store(store_type):
            return SampleCourseFactory.create()

    def _get_blocks(self, course, expected_mongo_queries):
        """
        Verifies the number of expected queries when calling
        get_blocks on the given course.
        """
        with check_mongo_calls(expected_mongo_queries):
            with self.assertNumQueries(2):
                get_blocks(self.request, course.location, self.user)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_query_counts_cached(self, store_type):
        course = self._create_course(store_type)
        self._get_blocks(course, expected_mongo_queries=0)

    @ddt.data(
        (ModuleStoreEnum.Type.mongo, 5),
        (ModuleStoreEnum.Type.split, 3),
    )
    @ddt.unpack
    def test_query_counts_uncached(self, store_type, expected_mongo_queries):
        course = self._create_course(store_type)
        clear_course_from_cache(course.id)
        self._get_blocks(course, expected_mongo_queries)
