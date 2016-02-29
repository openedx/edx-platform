"""
test utils
"""
import mock
from nose.plugins.attrib import attr

from student.roles import CourseCcxCoachRole
from student.tests.factories import (
    AdminFactory,
)
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import CourseFactory
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.ccx import utils
from lms.djangoapps.ccx.tests.factories import CcxFactory
from lms.djangoapps.ccx.tests.utils import CcxTestCase
from ccx_keys.locator import CCXLocator


@attr('shard_1')
class TestGetCCXFromCCXLocator(ModuleStoreTestCase):
    """Verify that get_ccx_from_ccx_locator functions properly"""
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """Set up a course, coach, ccx and user"""
        super(TestGetCCXFromCCXLocator, self).setUp()
        self.course = CourseFactory.create()
        coach = self.coach = AdminFactory.create()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(coach)

    def call_fut(self, course_id):
        """call the function under test in this test case"""
        from lms.djangoapps.ccx.utils import get_ccx_from_ccx_locator
        return get_ccx_from_ccx_locator(course_id)

    def test_non_ccx_locator(self):
        """verify that nothing is returned if locator is not a ccx locator
        """
        result = self.call_fut(self.course.id)
        self.assertEqual(result, None)

    def test_ccx_locator(self):
        """verify that the ccx is retuned if using a ccx locator
        """
        ccx = CcxFactory(course_id=self.course.id, coach=self.coach)
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        result = self.call_fut(course_key)
        self.assertEqual(result, ccx)


@attr('shard_1')
class TestGetCourseChapters(CcxTestCase):
    """
    Tests for the `get_course_chapters` util function
    """
    def setUp(self):
        """
        Set up tests
        """
        super(TestGetCourseChapters, self).setUp()
        self.course_key = self.course.location.course_key

    def test_get_structure_non_existing_key(self):
        """
        Test to get the course structure
        """
        self.assertEqual(utils.get_course_chapters(None), None)
        # build a fake key
        fake_course_key = CourseKey.from_string('course-v1:FakeOrg+CN1+CR-FALLNEVER1')
        self.assertEqual(utils.get_course_chapters(fake_course_key), None)

    @mock.patch('openedx.core.djangoapps.content.course_structures.models.CourseStructure.structure',
                new_callable=mock.PropertyMock)
    def test_wrong_course_structure(self, mocked_attr):
        """
        Test the case where the course  has an unexpected structure.
        """
        mocked_attr.return_value = {'foo': 'bar'}
        self.assertEqual(utils.get_course_chapters(self.course_key), [])

    def test_get_chapters(self):
        """
        Happy path
        """
        course_chapters = utils.get_course_chapters(self.course_key)
        self.assertEqual(len(course_chapters), 2)
        self.assertEqual(
            sorted(course_chapters),
            sorted([unicode(child) for child in self.course.children])
        )
