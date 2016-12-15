"""
Tests for Blocks api.py
"""

from django.test.client import RequestFactory

from course_blocks.tests.helpers import EnableTransformerRegistryMixin
from student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory

from ..api import get_blocks


class TestGetBlocks(EnableTransformerRegistryMixin, SharedModuleStoreTestCase):
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
