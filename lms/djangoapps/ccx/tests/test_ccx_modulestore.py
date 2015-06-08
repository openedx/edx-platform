"""
Test the CCXModulestoreWrapper
"""
from collections import deque
from ccx_keys.locator import CCXLocator, CCXBlockUsageLocator
import datetime
from itertools import izip_longest
import pytz
from student.tests.factories import (  # pylint: disable=import-error
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..models import CustomCourseForEdX


def flatten(seq):
    """
    For [[1, 2], [3, 4]] returns [1, 2, 3, 4].  Does not recurse.
    """
    return [x for sub in seq for x in sub]


class TestCCXModulestoreWrapper(ModuleStoreTestCase):
    """tests for a modulestore wrapped by CCXModulestoreWrapper
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(TestCCXModulestoreWrapper, self).setUp()
        course = CourseFactory.create()

        # Create instructor account
        coach = AdminFactory.create()

        # Create a course outline
        self.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC)
        self.mooc_due = due = datetime.datetime(
            2010, 7, 7, 0, 0, tzinfo=pytz.UTC)
        chapters = [ItemFactory.create(start=start, parent=course)
                    for _ in xrange(2)]
        sequentials = [
            ItemFactory.create(parent=c) for _ in xrange(2) for c in chapters
        ]
        verticals = [
            ItemFactory.create(
                due=due, parent=s, graded=True, format='Homework'
            ) for _ in xrange(2) for s in sequentials
        ]
        blocks = [
            ItemFactory.create(parent=v) for _ in xrange(2) for v in verticals
        ]

        self.ccx = ccx = CustomCourseForEdX(
            course_id=course.id,
            display_name='Test CCX',
            coach=coach
        )
        ccx.save()

        self.ccx_locator = CCXLocator.from_course_locator(course.id, ccx.id)

    def get_all_children_bf(self, block):
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
        for expected, actual in izip_longest(
            self.get_all_children_bf(course), self.get_all_children_bf(ccx)
        ):
            if expected is None:
                self.fail('course children exhausted before ccx children')
            if actual is None:
                self.fail('ccx children exhausted before course children')
            self.assertEqual(expected.display_name, actual.display_name)
            self.assertEqual(expected.location.course_key, course_key)
            self.assertEqual(actual.location.course_key, self.ccx_locator)

