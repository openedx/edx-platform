import courseware.access as access
import datetime

from mock import Mock

from django.test import TestCase
from django.test.utils import override_settings

from courseware.tests.factories import UserFactory, CourseEnrollmentAllowedFactory, StaffFactory, InstructorFactory
from student.tests.factories import AnonymousUserFactory
from xmodule.modulestore import Location
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
import pytz


# pylint: disable=protected-access
@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AccessTestCase(TestCase):
    """
    Tests for the various access controls on the student dashboard
    """

    def setUp(self):
        self.course = Location('i4x://edX/toy/course/2012_Fall')
        self.anonymous_user = AnonymousUserFactory()
        self.student = UserFactory()
        self.global_staff = UserFactory(is_staff=True)
        self.course_staff = StaffFactory(course=self.course)
        self.course_instructor = InstructorFactory(course=self.course)

    def test__has_access_to_location(self):
        self.assertFalse(access._has_access_to_location(None, self.course, 'staff', None))

        self.assertFalse(access._has_access_to_location(self.anonymous_user, self.course, 'staff', None))
        self.assertFalse(access._has_access_to_location(self.anonymous_user, self.course, 'instructor', None))

        self.assertTrue(access._has_access_to_location(self.global_staff, self.course, 'staff', None))
        self.assertTrue(access._has_access_to_location(self.global_staff, self.course, 'instructor', None))

        # A user has staff access if they are in the staff group
        self.assertTrue(access._has_access_to_location(self.course_staff, self.course, 'staff', None))
        self.assertFalse(access._has_access_to_location(self.course_staff, self.course, 'instructor', None))

        # A user has staff and instructor access if they are in the instructor group
        self.assertTrue(access._has_access_to_location(self.course_instructor, self.course, 'staff', None))
        self.assertTrue(access._has_access_to_location(self.course_instructor, self.course, 'instructor', None))

        # A user does not have staff or instructor access if they are
        # not in either the staff or the the instructor group
        self.assertFalse(access._has_access_to_location(self.student, self.course, 'staff', None))
        self.assertFalse(access._has_access_to_location(self.student, self.course, 'instructor', None))

    def test__has_access_string(self):
        u = Mock(is_staff=True)
        self.assertFalse(access._has_access_string(u, 'not_global', 'staff', None))

        u._has_global_staff_access.return_value = True
        self.assertTrue(access._has_access_string(u, 'global', 'staff', None))

        self.assertRaises(ValueError, access._has_access_string, u, 'global', 'not_staff', None)

    def test__has_access_descriptor(self):
        # TODO: override DISABLE_START_DATES and test the start date branch of the method
        u = Mock()
        d = Mock()
        d.category = 'course'
        d.start = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)  # make sure the start time is in the past

        # Always returns true because DISABLE_START_DATES is set in test.py
        self.assertTrue(access._has_access_descriptor(u, d, 'load'))
        self.assertRaises(ValueError, access._has_access_descriptor, u, d, 'not_load_or_staff')

    def test__has_access_course_desc_can_enroll(self):
        u = Mock()
        yesterday = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
        c = Mock(enrollment_start=yesterday, enrollment_end=tomorrow, enrollment_domain='')

        # User can enroll if it is between the start and end dates
        self.assertTrue(access._has_access_course_desc(u, c, 'enroll'))

        # User can enroll if authenticated and specifically allowed for that course
        # even outside the open enrollment period
        u = Mock(email='test@edx.org', is_staff=False)
        u.is_authenticated.return_value = True

        c = Mock(enrollment_start=tomorrow, enrollment_end=tomorrow, id='edX/test/2012_Fall', enrollment_domain='')

        allowed = CourseEnrollmentAllowedFactory(email=u.email, course_id=c.id)

        self.assertTrue(access._has_access_course_desc(u, c, 'enroll'))

        # Staff can always enroll even outside the open enrollment period
        u = Mock(email='test@edx.org', is_staff=True)
        u.is_authenticated.return_value = True

        c = Mock(enrollment_start=tomorrow, enrollment_end=tomorrow, id='edX/test/Whenever', enrollment_domain='')
        self.assertTrue(access._has_access_course_desc(u, c, 'enroll'))

        # TODO:
        # Non-staff cannot enroll outside the open enrollment period if not specifically allowed

    def test__user_passed_as_none(self):
        """Ensure has_access handles a user being passed as null"""
        access.has_access(None, 'global', 'staff', None)
