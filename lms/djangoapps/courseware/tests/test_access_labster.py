# -*- coding: utf-8 -*-
"""
Test labster for the access control framework
"""
from ccx_keys.locator import CCXLocator
import courseware.access as access
from student.models import CourseEnrollment
from ccx.tests.factories import CcxFactory
from courseware.tests.factories import InstructorFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import (
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE
)

# pylint: disable=protected-access

class UserRoleTestCase(SharedModuleStoreTestCase):
    """
    Tests for user roles.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(UserRoleTestCase, self).setUp()

        # setup course and user
        self.course = CourseFactory.create()
        self.course2 = CourseFactory.create()
        self.course_instructor = InstructorFactory(course_key=self.course.id, password="test")
        self.course_instructor2 = InstructorFactory(course_key=self.course2.id, password="test")

    def test_user_role_instructor(self):
        """
        Ensure that user role is instructor in the course.
        """
        self.assertEqual(
            'instructor',
            access.get_user_role(self.course_instructor, self.course.id)
        )
        self.assertEqual(
            'instructor',
            access.get_user_role(self.course_instructor2, self.course2.id)
        )

    def test_user_role_instructor_as_role_student(self):
        """
        Ensure that user role instructor is student when the instructor is joining in another course.
        """
        # create ccx
        ccx = CcxFactory(course_id=self.course.id)
        ccx_locator = CCXLocator.from_course_locator(self.course.id, ccx.id)
        CourseEnrollment.enroll(self.course_instructor2, ccx_locator)

        # Test for role of a instructor in course
        self.assertEqual(
            'instructor',
            access.get_user_role(self.course_instructor, self.course.id)
        )

        # Test for role of a student in course
        self.assertEqual(
            'student',
            access.get_user_role(self.course_instructor2, self.course.id)
        )