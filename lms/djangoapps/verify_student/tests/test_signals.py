"""
Unit tests for the VerificationDeadline signals
"""

from datetime import datetime, timedelta

from pytz import UTC
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.verify_student.models import VerificationDeadline
from lms.djangoapps.verify_student.signals import _listen_for_course_publish


class VerificationDeadlineSignalTest(ModuleStoreTestCase):
    """
    Tests for the VerificationDeadline signal
    """

    def setUp(self):
        super(VerificationDeadlineSignalTest, self).setUp()
        self.end = datetime.now(tz=UTC).replace(microsecond=0) + timedelta(days=7)
        self.course = CourseFactory.create(end=self.end)
        VerificationDeadline.objects.all().delete()

    def test_no_deadline(self):
        """ Verify the signal sets deadline to course end when no deadline exists."""
        _listen_for_course_publish('store', self.course.id)

        self.assertEqual(VerificationDeadline.deadline_for_course(self.course.id), self.course.end)

    def test_deadline(self):
        """ Verify deadline is set to course end date by signal when changed. """
        deadline = datetime.now(tz=UTC) - timedelta(days=7)
        VerificationDeadline.set_deadline(self.course.id, deadline)

        _listen_for_course_publish('store', self.course.id)
        self.assertEqual(VerificationDeadline.deadline_for_course(self.course.id), self.course.end)

    def test_deadline_explicit(self):
        """ Verify deadline is unchanged by signal when explicitly set. """
        deadline = datetime.now(tz=UTC) - timedelta(days=7)
        VerificationDeadline.set_deadline(self.course.id, deadline, is_explicit=True)

        _listen_for_course_publish('store', self.course.id)

        actual_deadline = VerificationDeadline.deadline_for_course(self.course.id)
        self.assertNotEqual(actual_deadline, self.course.end)
        self.assertEqual(actual_deadline, deadline)
