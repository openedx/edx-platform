"""
tests for the models
"""
from datetime import datetime, timedelta
from django.utils.timezone import UTC
from mock import patch
from nose.plugins.attrib import attr
from student.models import CourseEnrollment  # pylint: disable=import-error
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
from student.tests.factories import (  # pylint: disable=import-error
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)
from util.tests.test_date_utils import fake_ugettext
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    check_mongo_calls
)

from .factories import (
    CcxFactory,
    CcxFutureMembershipFactory,
)
from ..models import (
    CcxMembership,
    CcxFutureMembership,
)
from ..overrides import override_field_for_ccx


@attr('shard_1')
class TestCcxMembership(ModuleStoreTestCase):
    """Unit tests for the CcxMembership model
    """

    def setUp(self):
        """common setup for all tests"""
        super(TestCcxMembership, self).setUp()
        self.course = course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        enrollment = CourseEnrollmentFactory.create(course_id=course.id)
        self.enrolled_user = enrollment.user
        self.unenrolled_user = UserFactory.create()

    def create_future_enrollment(self, user, auto_enroll=True):
        """
        utility method to create future enrollment
        """
        pfm = CcxFutureMembershipFactory.create(
            ccx=self.ccx,
            email=user.email,
            auto_enroll=auto_enroll
        )
        return pfm

    def has_course_enrollment(self, user):
        """
        utility method to create future enrollment
        """
        enrollment = CourseEnrollment.objects.filter(
            user=user, course_id=self.course.id
        )
        return enrollment.exists()

    def has_ccx_membership(self, user):
        """
        verify ccx membership
        """
        membership = CcxMembership.objects.filter(
            student=user, ccx=self.ccx, active=True
        )
        return membership.exists()

    def has_ccx_future_membership(self, user):
        """
        verify future ccx membership
        """
        future_membership = CcxFutureMembership.objects.filter(
            email=user.email, ccx=self.ccx
        )
        return future_membership.exists()

    def call_mut(self, student, future_membership):
        """
        Call the method undser test
        """
        CcxMembership.auto_enroll(student, future_membership)

    def test_ccx_auto_enroll_unregistered_user(self):
        """verify auto_enroll works when user is not enrolled in the MOOC

        n.b.  After auto_enroll, user will have both a MOOC enrollment and a
              CCX membership
        """
        user = self.unenrolled_user
        pfm = self.create_future_enrollment(user)
        self.assertTrue(self.has_ccx_future_membership(user))
        self.assertFalse(self.has_course_enrollment(user))
        # auto_enroll user
        self.call_mut(user, pfm)

        self.assertTrue(self.has_course_enrollment(user))
        self.assertTrue(self.has_ccx_membership(user))
        self.assertFalse(self.has_ccx_future_membership(user))

    def test_ccx_auto_enroll_registered_user(self):
        """verify auto_enroll works when user is enrolled in the MOOC
        """
        user = self.enrolled_user
        pfm = self.create_future_enrollment(user)
        self.assertTrue(self.has_ccx_future_membership(user))
        self.assertTrue(self.has_course_enrollment(user))

        self.call_mut(user, pfm)

        self.assertTrue(self.has_course_enrollment(user))
        self.assertTrue(self.has_ccx_membership(user))
        self.assertFalse(self.has_ccx_future_membership(user))

    def test_future_membership_disallows_auto_enroll(self):
        """verify that the CcxFutureMembership can veto auto_enroll
        """
        user = self.unenrolled_user
        pfm = self.create_future_enrollment(user, auto_enroll=False)
        self.assertTrue(self.has_ccx_future_membership(user))
        self.assertFalse(self.has_course_enrollment(user))

        self.assertRaises(ValueError, self.call_mut, user, pfm)

        self.assertFalse(self.has_course_enrollment(user))
        self.assertFalse(self.has_ccx_membership(user))
        self.assertTrue(self.has_ccx_future_membership(user))


@attr('shard_1')
class TestCCX(ModuleStoreTestCase):
    """Unit tests for the CustomCourseForEdX model
    """

    def setUp(self):
        """common setup for all tests"""
        super(TestCCX, self).setUp()
        self.course = course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)

    def set_ccx_override(self, field, value):
        """Create a field override for the test CCX on <field> with <value>"""
        override_field_for_ccx(self.ccx, self.course, field, value)

    def test_ccx_course_is_correct_course(self):
        """verify that the course property of a ccx returns the right course"""
        expected = self.course
        actual = self.ccx.course
        self.assertEqual(expected, actual)

    def test_ccx_course_caching(self):
        """verify that caching the propery works to limit queries"""
        with check_mongo_calls(1):
            # these statements are used entirely to demonstrate the
            # instance-level caching of these values on CCX objects. The
            # check_mongo_calls context is the point here.
            self.ccx.course  # pylint: disable=pointless-statement
        with check_mongo_calls(0):
            self.ccx.course  # pylint: disable=pointless-statement

    def test_ccx_start_is_correct(self):
        """verify that the start datetime for a ccx is correctly retrieved

        Note that after setting the start field override microseconds are
        truncated, so we can't do a direct comparison between before and after.
        For this reason we test the difference between and make sure it is less
        than one second.
        """
        expected = datetime.now(UTC())
        self.set_ccx_override('start', expected)
        actual = self.ccx.start  # pylint: disable=no-member
        diff = expected - actual
        self.assertTrue(abs(diff.total_seconds()) < 1)

    def test_ccx_start_caching(self):
        """verify that caching the start property works to limit queries"""
        now = datetime.now(UTC())
        self.set_ccx_override('start', now)
        with check_mongo_calls(1):
            # these statements are used entirely to demonstrate the
            # instance-level caching of these values on CCX objects. The
            # check_mongo_calls context is the point here.
            self.ccx.start  # pylint: disable=pointless-statement, no-member
        with check_mongo_calls(0):
            self.ccx.start  # pylint: disable=pointless-statement, no-member

    def test_ccx_due_without_override(self):
        """verify that due returns None when the field has not been set"""
        actual = self.ccx.due  # pylint: disable=no-member
        self.assertIsNone(actual)

    def test_ccx_due_is_correct(self):
        """verify that the due datetime for a ccx is correctly retrieved"""
        expected = datetime.now(UTC())
        self.set_ccx_override('due', expected)
        actual = self.ccx.due  # pylint: disable=no-member
        diff = expected - actual
        self.assertTrue(abs(diff.total_seconds()) < 1)

    def test_ccx_due_caching(self):
        """verify that caching the due property works to limit queries"""
        expected = datetime.now(UTC())
        self.set_ccx_override('due', expected)
        with check_mongo_calls(1):
            # these statements are used entirely to demonstrate the
            # instance-level caching of these values on CCX objects. The
            # check_mongo_calls context is the point here.
            self.ccx.due  # pylint: disable=pointless-statement, no-member
        with check_mongo_calls(0):
            self.ccx.due  # pylint: disable=pointless-statement, no-member

    def test_ccx_has_started(self):
        """verify that a ccx marked as starting yesterday has started"""
        now = datetime.now(UTC())
        delta = timedelta(1)
        then = now - delta
        self.set_ccx_override('start', then)
        self.assertTrue(self.ccx.has_started())  # pylint: disable=no-member

    def test_ccx_has_not_started(self):
        """verify that a ccx marked as starting tomorrow has not started"""
        now = datetime.now(UTC())
        delta = timedelta(1)
        then = now + delta
        self.set_ccx_override('start', then)
        self.assertFalse(self.ccx.has_started())  # pylint: disable=no-member

    def test_ccx_has_ended(self):
        """verify that a ccx that has a due date in the past has ended"""
        now = datetime.now(UTC())
        delta = timedelta(1)
        then = now - delta
        self.set_ccx_override('due', then)
        self.assertTrue(self.ccx.has_ended())  # pylint: disable=no-member

    def test_ccx_has_not_ended(self):
        """verify that a ccx that has a due date in the future has not eneded
        """
        now = datetime.now(UTC())
        delta = timedelta(1)
        then = now + delta
        self.set_ccx_override('due', then)
        self.assertFalse(self.ccx.has_ended())  # pylint: disable=no-member

    def test_ccx_without_due_date_has_not_ended(self):
        """verify that a ccx without a due date has not ended"""
        self.assertFalse(self.ccx.has_ended())  # pylint: disable=no-member

    # ensure that the expected localized format will be found by the i18n
    # service
    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "SHORT_DATE_FORMAT": "%b %d, %Y",
    }))
    def test_start_datetime_short_date(self):
        """verify that the start date for a ccx formats properly by default"""
        start = datetime(2015, 1, 1, 12, 0, 0, tzinfo=UTC())
        expected = "Jan 01, 2015"
        self.set_ccx_override('start', start)
        actual = self.ccx.start_datetime_text()  # pylint: disable=no-member
        self.assertEqual(expected, actual)

    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "DATE_TIME_FORMAT": "%b %d, %Y at %H:%M",
    }))
    def test_start_datetime_date_time_format(self):
        """verify that the DATE_TIME format also works as expected"""
        start = datetime(2015, 1, 1, 12, 0, 0, tzinfo=UTC())
        expected = "Jan 01, 2015 at 12:00 UTC"
        self.set_ccx_override('start', start)
        actual = self.ccx.start_datetime_text('DATE_TIME')  # pylint: disable=no-member
        self.assertEqual(expected, actual)

    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "SHORT_DATE_FORMAT": "%b %d, %Y",
    }))
    def test_end_datetime_short_date(self):
        """verify that the end date for a ccx formats properly by default"""
        end = datetime(2015, 1, 1, 12, 0, 0, tzinfo=UTC())
        expected = "Jan 01, 2015"
        self.set_ccx_override('due', end)
        actual = self.ccx.end_datetime_text()  # pylint: disable=no-member
        self.assertEqual(expected, actual)

    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "DATE_TIME_FORMAT": "%b %d, %Y at %H:%M",
    }))
    def test_end_datetime_date_time_format(self):
        """verify that the DATE_TIME format also works as expected"""
        end = datetime(2015, 1, 1, 12, 0, 0, tzinfo=UTC())
        expected = "Jan 01, 2015 at 12:00 UTC"
        self.set_ccx_override('due', end)
        actual = self.ccx.end_datetime_text('DATE_TIME')  # pylint: disable=no-member
        self.assertEqual(expected, actual)

    @patch('util.date_utils.ugettext', fake_ugettext(translations={
        "DATE_TIME_FORMAT": "%b %d, %Y at %H:%M",
    }))
    def test_end_datetime_no_due_date(self):
        """verify that without a due date, the end date is an empty string"""
        expected = ''
        actual = self.ccx.end_datetime_text()  # pylint: disable=no-member
        self.assertEqual(expected, actual)
        actual = self.ccx.end_datetime_text('DATE_TIME')  # pylint: disable=no-member
        self.assertEqual(expected, actual)
