# -*- coding: utf-8 -*-
"""
Test labster for the access control framework
"""
from ccx_keys.locator import CCXLocator
from student.models import CourseEnrollment
from student.roles import CourseCcxCoachRole
from courseware.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import (
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)
import courseware.access as access
from lms.djangoapps.ccx.models import CustomCourseForEdX


class UserRoleTestCase(SharedModuleStoreTestCase):
    """
    Tests for user roles.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def make_coach(self, user, course_key):
        """
        Create coach user.
        """
        role = CourseCcxCoachRole(course_key)
        role.add_users(user)

    def make_ccx(self, coach, course, display_name):
        """
        Create ccx.
        """
        ccx = CustomCourseForEdX(
            course_id=course.id,
            coach=coach,
            display_name=display_name
        )
        ccx.save()

        ccx_locator = CCXLocator.from_course_locator(course.id, unicode(ccx.id))
        CourseEnrollment.enroll(coach, ccx_locator)

        return ccx_locator

    def setUp(self):
        """
        Set up tests.
        """
        super(UserRoleTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.course2 = CourseFactory.create()

        # Create coach account
        self.coach = UserFactory.create(password="test")
        self.coach2 = UserFactory.create(password="test")

        # Create ccx
        self.ccx_locator = self.make_ccx(self.coach, self.course, "Test CCX")
        self.ccx_locator2 = self.make_ccx(self.coach2, self.course2, "Test CCX2")

        # assign role to coach
        self.make_coach(self.coach, self.course.id)
        self.make_coach(self.coach2, self.course2.id)

    def test_user_role_instructor(self):
        """
        Ensure that user role is instructor in the course.
        """
        # User have access as coach on ccx
        self.assertEqual(
            'instructor',
            access.get_user_role(self.coach, self.ccx_locator)
        )
        self.assertEqual(
            'instructor',
            access.get_user_role(self.coach2, self.ccx_locator2)
        )

    def test_user_role_instructor_as_role_student(self):
        """
        Ensure that user role instructor is student when the instructor is joining in another course.
        """
        # Enroll user
        CourseEnrollment.enroll(self.coach2, self.ccx_locator)

        # Test for role of a instructor in course
        self.assertEqual(
            'instructor',
            access.get_user_role(self.coach, self.ccx_locator)
        )

        # Test for role of a student in course
        self.assertEqual(
            'student',
            access.get_user_role(self.coach2, self.ccx_locator)
        )
