"""
test utils
"""
from nose.plugins.attrib import attr

from ccx_keys.locator import CCXLocator
from student.roles import (
    CourseCcxCoachRole,
    CourseInstructorRole,
    CourseStaffRole,
)
from student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory
)
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore

from lms.djangoapps.instructor.access import list_with_level, allow_access

from lms.djangoapps.ccx.utils import add_master_course_staff_to_ccx
from lms.djangoapps.ccx.views import ccx_course
from lms.djangoapps.ccx.tests.factories import CcxFactory
from lms.djangoapps.ccx.tests.utils import CcxTestCase


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


class TestStaffOnCCX(CcxTestCase, SharedModuleStoreTestCase):
    """
    Tests for staff on ccx courses.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(TestStaffOnCCX, self).setUp()

        # Create instructor account
        self.client.login(username=self.coach.username, password="test")

        # create an instance of modulestore
        self.mstore = modulestore()

        # adding staff to master course.
        staff = UserFactory()
        allow_access(self.course, staff, 'staff')
        self.assertTrue(CourseStaffRole(self.course.id).has_user(staff))

        # adding instructor to master course.
        instructor = UserFactory()
        allow_access(self.course, instructor, 'instructor')
        self.assertTrue(CourseInstructorRole(self.course.id).has_user(instructor))

    def test_add_master_course_staff_to_ccx(self):
        """
        Test add staff of master course to ccx course
        """
        self.make_coach()
        ccx = self.make_ccx()
        ccx_locator = CCXLocator.from_course_locator(self.course.id, ccx.id)
        add_master_course_staff_to_ccx(self.course, ccx_locator, ccx.display_name)

        # assert that staff and instructors of master course has staff and instructor roles on ccx
        list_staff_master_course = list_with_level(self.course, 'staff')
        list_instructor_master_course = list_with_level(self.course, 'instructor')

        with ccx_course(ccx_locator) as course_ccx:
            list_staff_ccx_course = list_with_level(course_ccx, 'staff')
            self.assertEqual(len(list_staff_master_course), len(list_staff_ccx_course))
            self.assertEqual(list_staff_master_course[0].email, list_staff_ccx_course[0].email)

            list_instructor_ccx_course = list_with_level(course_ccx, 'instructor')
            self.assertEqual(len(list_instructor_ccx_course), len(list_instructor_master_course))
            self.assertEqual(list_instructor_ccx_course[0].email, list_instructor_master_course[0].email)
