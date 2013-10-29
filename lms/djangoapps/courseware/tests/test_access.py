from mock import Mock

from django.test import TestCase
from django.test.utils import override_settings

from xmodule.modulestore import Location
import courseware.access as access
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from .factories import CourseEnrollmentAllowedFactory
import datetime
from django.utils.timezone import UTC

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AccessTestCase(TestCase):
    def test__has_global_staff_access(self):
        u = Mock(is_staff=False)
        self.assertFalse(access._has_global_staff_access(u))

        u = Mock(is_staff=True)
        self.assertTrue(access._has_global_staff_access(u))

    def test__has_access_to_location(self):
        location = Location('i4x://edX/toy/course/2012_Fall')

        self.assertFalse(access._has_access_to_location(None, location,
                                                        'staff', None))
        u = Mock()
        u.is_authenticated.return_value = False
        self.assertFalse(access._has_access_to_location(u, location,
                                                        'staff', None))
        u = Mock(is_staff=True)
        self.assertTrue(access._has_access_to_location(u, location,
                                                       'instructor', None))
        # A user has staff access if they are in the staff group
        u = Mock(is_staff=False)
        g = Mock()
        g.name = 'staff_edX/toy/2012_Fall'
        u.groups.all.return_value = [g]
        self.assertTrue(access._has_access_to_location(u, location,
                                                        'staff', None))
        # A user has staff access if they are in the instructor group
        g.name = 'instructor_edX/toy/2012_Fall'
        self.assertTrue(access._has_access_to_location(u, location,
                                                        'staff', None))

        # A user has instructor access if they are in the instructor group
        g.name = 'instructor_edX/toy/2012_Fall'
        self.assertTrue(access._has_access_to_location(u, location,
                                                        'instructor', None))

        # A user does not have staff access if they are
        # not in either the staff or the the instructor group
        g.name = 'student_only'
        self.assertFalse(access._has_access_to_location(u, location,
                                                        'staff', None))

        # A user does not have instructor access if they are
        # not in the instructor group
        g.name = 'student_only'
        self.assertFalse(access._has_access_to_location(u, location,
                                                        'instructor', None))

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
        d.start = datetime.datetime.now(UTC()) - datetime.timedelta(days=1)  # make sure the start time is in the past

        # Always returns true because DISABLE_START_DATES is set in test.py
        self.assertTrue(access._has_access_descriptor(u, d, 'load'))
        self.assertRaises(ValueError, access._has_access_descriptor, u, d, 'not_load_or_staff')

    def test__has_access_course_desc_can_enroll(self):
        u = Mock()
        yesterday = datetime.datetime.now(UTC()) - datetime.timedelta(days=1)
        tomorrow = datetime.datetime.now(UTC()) + datetime.timedelta(days=1)
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

    def test__has_access_refund(self):
        user = UserFactory.create()
        course = CourseFactory.create(org='org', number='test', run='course', display_name='Test Course')
        today = datetime.datetime.now(UTC())
        grace_period = datetime.timedelta(days=14)
        one_day_extra = datetime.timedelta(days=1)

        # User is allowed to receive refund if it is within two weeks of course start date
        course.enrollment_start = (today - one_day_extra)
        self.assertTrue(access._has_access_course_desc(user, course, 'refund'))

        course.enrollment_start = (today - grace_period)
        self.assertTrue(access._has_access_course_desc(user, course, 'refund'))

        # After two weeks, user may no longer receive a refund
        course.enrollment_start = (today - grace_period - one_day_extra)
        self.assertFalse(access._has_access_course_desc(user, course, 'refund'))
