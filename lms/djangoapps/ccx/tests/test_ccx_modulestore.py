"""
Test the CCXModulestoreWrapper
"""
from collections import deque
from ccx_keys.locator import CCXLocator
import datetime
from itertools import izip_longest, chain
import pytz
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import (
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..models import CustomCourseForEdX


class TestCCXModulestoreWrapper(SharedModuleStoreTestCase):
    """tests for a modulestore wrapped by CCXModulestoreWrapper
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(TestCCXModulestoreWrapper, cls).setUpClass()
        cls.course = course = CourseFactory.create()
        cls.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC
        )
        cls.mooc_due = due = datetime.datetime(
            2010, 7, 7, 0, 0, tzinfo=pytz.UTC
        )
        # Create a course outline
        cls.chapters = chapters = [
            ItemFactory.create(start=start, parent=course) for _ in xrange(2)
        ]
        cls.sequentials = sequentials = [
            ItemFactory.create(parent=c) for _ in xrange(2) for c in chapters
        ]
        cls.verticals = verticals = [
            ItemFactory.create(
                due=due, parent=s, graded=True, format='Homework'
            ) for _ in xrange(2) for s in sequentials
        ]
        cls.blocks = [
            ItemFactory.create(parent=v, category='html') for _ in xrange(2) for v in verticals
        ]

    def setUp(self):
        """
        Set up tests
        """
        super(TestCCXModulestoreWrapper, self).setUp()
        self.user = UserFactory.create()

        # Create instructor account
        coach = AdminFactory.create()

        self.ccx = ccx = CustomCourseForEdX(
            course_id=self.course.id,
            display_name='Test CCX',
            coach=coach
        )
        ccx.save()

        self.ccx_locator = CCXLocator.from_course_locator(self.course.id, ccx.id)  # pylint: disable=no-member

    def get_all_children_bf(self, block):
        """traverse the children of block in a breadth-first order"""
        queue = deque([block])
        while queue:
            item = queue.popleft()
            yield item
            queue.extend(item.get_children())

    def get_course(self, key):
        """get a course given a key"""
        with self.store.bulk_operations(key):
            course = self.store.get_course(key)
        return course

    def test_get_course(self):
        """retrieving a course with a ccx key works"""
        expected = self.get_course(self.ccx_locator.to_course_locator())
        actual = self.get_course(self.ccx_locator)
        self.assertEqual(
            expected.location.course_key,
            actual.location.course_key.to_course_locator())
        self.assertEqual(expected.display_name, actual.display_name)

    def test_get_children(self):
        """the children of retrieved courses should be the same with course and ccx keys
        """
        course_key = self.ccx_locator.to_course_locator()
        course = self.get_course(course_key)
        ccx = self.get_course(self.ccx_locator)
        test_fodder = izip_longest(
            self.get_all_children_bf(course), self.get_all_children_bf(ccx)
        )
        for expected, actual in test_fodder:
            if expected is None:
                self.fail('course children exhausted before ccx children')
            if actual is None:
                self.fail('ccx children exhausted before course children')
            self.assertEqual(expected.display_name, actual.display_name)
            self.assertEqual(expected.location.course_key, course_key)
            self.assertEqual(actual.location.course_key, self.ccx_locator)

    def test_has_item(self):
        """can verify that a location exists, using ccx block usage key"""
        for item in chain(self.chapters, self.sequentials, self.verticals, self.blocks):
            block_key = self.ccx_locator.make_usage_key(
                item.location.block_type, item.location.block_id
            )
            self.assertTrue(self.store.has_item(block_key))

    def test_get_item(self):
        """can retrieve an item by a location key, using a ccx block usage key

        the retrieved item should be the same as the the one read without ccx
        info
        """
        for expected in chain(self.chapters, self.sequentials, self.verticals, self.blocks):
            block_key = self.ccx_locator.make_usage_key(
                expected.location.block_type, expected.location.block_id
            )
            actual = self.store.get_item(block_key)
            self.assertEqual(expected.display_name, actual.display_name)
            self.assertEqual(expected.location, actual.location.to_block_locator())

    def test_publication_api(self):
        """verify that we can correctly discern a published item by ccx key"""
        for expected in self.blocks:
            block_key = self.ccx_locator.make_usage_key(
                expected.location.block_type, expected.location.block_id
            )
            self.assertTrue(self.store.has_published_version(expected))
            self.store.unpublish(block_key, self.user.id)
            self.assertFalse(self.store.has_published_version(expected))
            self.store.publish(block_key, self.user.id)
            self.assertTrue(self.store.has_published_version(expected))
