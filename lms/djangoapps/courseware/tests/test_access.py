import courseware.access as access
import datetime

from mock import Mock

from django.test import TestCase
from django.test.utils import override_settings

from courseware.tests.factories import UserFactory, StaffFactory, InstructorFactory
from student.tests.factories import AnonymousUserFactory, CourseEnrollmentAllowedFactory
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
import pytz
from xmodule.modulestore.locations import SlashSeparatedCourseKey


# pylint: disable=protected-access
@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AccessTestCase(TestCase):
    """
    Tests for the various access controls on the student dashboard
    """

    def setUp(self):
        course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.course = course_key.make_usage_key('course', course_key.run)
        self.anonymous_user = AnonymousUserFactory()
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course_key=self.course.course_key)
        self.course_instructor = InstructorFactory(course_key=self.course.course_key)

    def test_has_access_to_course(self):
        self.assertFalse(access._has_access_to_course(
            None, 'staff', self.course.course_key
        ))

        self.assertFalse(access._has_access_to_course(
            self.anonymous_user, 'staff', self.course.course_key
        ))
        self.assertFalse(access._has_access_to_course(
            self.anonymous_user, 'instructor', self.course.course_key
        ))

        self.assertTrue(access._has_access_to_course(
            self.global_staff, 'staff', self.course.course_key
        ))
        self.assertTrue(access._has_access_to_course(
            self.global_staff, 'instructor', self.course.course_key
        ))

        # A user has staff access if they are in the staff group
        self.assertTrue(access._has_access_to_course(
            self.course_staff, 'staff', self.course.course_key
        ))
        self.assertFalse(access._has_access_to_course(
            self.course_staff, 'instructor', self.course.course_key
        ))

        # A user has staff and instructor access if they are in the instructor group
        self.assertTrue(access._has_access_to_course(
            self.course_instructor, 'staff', self.course.course_key
        ))
        self.assertTrue(access._has_access_to_course(
            self.course_instructor, 'instructor', self.course.course_key
        ))

        # A user does not have staff or instructor access if they are
        # not in either the staff or the the instructor group
        self.assertFalse(access._has_access_to_course(
            self.student, 'staff', self.course.course_key
        ))
        self.assertFalse(access._has_access_to_course(
            self.student, 'instructor', self.course.course_key
        ))

    def test__has_access_string(self):
        user = Mock(is_staff=True)
        self.assertFalse(access._has_access_string(user, 'staff', 'not_global', self.course.course_key))

        user._has_global_staff_access.return_value = True
        self.assertTrue(access._has_access_string(user, 'staff', 'global', self.course.course_key))

        self.assertRaises(ValueError, access._has_access_string, user, 'not_staff', 'global', self.course.course_key)

    def test__has_access_descriptor(self):
        # TODO: override DISABLE_START_DATES and test the start date branch of the method
        user = Mock()
        date = Mock()
        date.start = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)  # make sure the start time is in the past

        # Always returns true because DISABLE_START_DATES is set in test.py
        self.assertTrue(access._has_access_descriptor(user, 'load', date))
        self.assertTrue(access._has_access_descriptor(user, 'instructor', date))
        with self.assertRaises(ValueError):
            access._has_access_descriptor(user, 'not_load_or_staff', date)

    def test__has_access_course_desc_can_enroll(self):
        user = Mock()
        yesterday = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
        course = Mock(enrollment_start=yesterday, enrollment_end=tomorrow, enrollment_domain='')

        # User can enroll if it is between the start and end dates
        self.assertTrue(access._has_access_course_desc(user, 'enroll', course))

        # User can enroll if authenticated and specifically allowed for that course
        # even outside the open enrollment period
        user = Mock(email='test@edx.org', is_staff=False)
        user.is_authenticated.return_value = True

        course = Mock(
            enrollment_start=tomorrow, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', '2012_Fall'), enrollment_domain=''
        )

        CourseEnrollmentAllowedFactory(email=user.email, course_id=course.id)

        self.assertTrue(access._has_access_course_desc(user, 'enroll', course))

        # Staff can always enroll even outside the open enrollment period
        user = Mock(email='test@edx.org', is_staff=True)
        user.is_authenticated.return_value = True

        course = Mock(
            enrollment_start=tomorrow, enrollment_end=tomorrow,
            id=SlashSeparatedCourseKey('edX', 'test', 'Whenever'), enrollment_domain='',
        )
        self.assertTrue(access._has_access_course_desc(user, 'enroll', course))

        # TODO:
        # Non-staff cannot enroll outside the open enrollment period if not specifically allowed

    def test__user_passed_as_none(self):
        """Ensure has_access handles a user being passed as null"""
        access.has_access(None, 'staff', 'global', None)


class UserRoleTestCase(TestCase):
    """
    Tests for user roles.
    """
    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.anonymous_user = AnonymousUserFactory()
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course_key=self.course_key)
        self.course_instructor = InstructorFactory(course_key=self.course_key)

    def test_user_role_staff(self):
        """Ensure that user role is student for staff masqueraded as student."""
        self.assertEqual(
            'staff',
            access.get_user_role(self.course_staff, self.course_key)
        )
        # Masquerade staff
        self.course_staff.masquerade_as_student = True
        self.assertEqual(
            'student',
            access.get_user_role(self.course_staff, self.course_key)
        )

    def test_user_role_instructor(self):
        """Ensure that user role is student for instructor masqueraded as student."""
        self.assertEqual(
            'instructor',
            access.get_user_role(self.course_instructor, self.course_key)
        )
        # Masquerade instructor
        self.course_instructor.masquerade_as_student = True
        self.assertEqual(
            'student',
            access.get_user_role(self.course_instructor, self.course_key)
        )

    def test_user_role_anonymous(self):
        """Ensure that user role is student for anonymous user."""
        self.assertEqual(
            'student',
            access.get_user_role(self.anonymous_user, self.course_key)
        )
