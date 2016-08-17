"""
tests for the models
"""
from datetime import datetime, timedelta
from django.utils.timezone import UTC
from mock import patch
from nose.plugins.attrib import attr
from student.roles import CourseCcxCoachRole
from student.tests.factories import (
    AdminFactory,
)
from util.tests.test_date_utils import fake_ugettext
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    check_mongo_calls
)

from .factories import (
    CcxFactory,
)
from ..overrides import override_field_for_ccx


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
        self.assertLess(abs(diff.total_seconds()), 1)

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
        self.assertLess(abs(diff.total_seconds()), 1)

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

    def test_ccx_max_student_enrollment_correct(self):
        """
        Verify the override value for max_student_enrollments_allowed
        """
        expected = 200
        self.set_ccx_override('max_student_enrollments_allowed', expected)
        actual = self.ccx.max_student_enrollments_allowed  # pylint: disable=no-member
        self.assertEqual(expected, actual)
