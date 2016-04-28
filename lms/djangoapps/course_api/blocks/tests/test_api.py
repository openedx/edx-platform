"""
Tests for Blocks api.py
"""

from django.test.client import RequestFactory
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory

from ..api import get_blocks


class TestGetBlocks(ModuleStoreTestCase):
    """
    Tests for the get_blocks function
    """
    def setUp(self):
        super(TestGetBlocks, self).setUp()
        self.course = SampleCourseFactory.create()
        self.user = UserFactory.create()
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user

    def test_basic(self):
        blocks = get_blocks(self.request, self.course.location, self.user)
        self.assertEquals(blocks['root'], unicode(self.course.location))
        # add 1 for the orphaned course about block
        self.assertEquals(len(blocks['blocks']) + 1, len(self.store.get_items(self.course.id)))

    def test_no_user(self):
        with self.assertRaises(NotImplementedError):
            get_blocks(self.request, self.course.location)
