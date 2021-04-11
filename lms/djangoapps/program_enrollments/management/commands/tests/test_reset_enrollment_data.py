"""
Tests for the reset_enrollment_data management command.
"""


import sys
from contextlib import contextmanager
from uuid import uuid4

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from six import StringIO

from lms.djangoapps.program_enrollments.management.commands import reset_enrollment_data
from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from lms.djangoapps.program_enrollments.tests.factories import ProgramCourseEnrollmentFactory, ProgramEnrollmentFactory
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory


class TestResetEnrollmentData(TestCase):
    """ Test reset_enrollment_data command """

    @classmethod
    def setUpClass(cls):
        super(TestResetEnrollmentData, cls).setUpClass()
        cls.command = reset_enrollment_data.Command()
        cls.program_uuid = uuid4()

    def setUp(self):
        super(TestResetEnrollmentData, self).setUp()
        self.user = UserFactory()

    @contextmanager
    def _replace_stdin(self, text):
        """
        Mock out standard input to return `text` when read from.
        """
        orig = sys.stdin
        sys.stdin = StringIO(text)
        yield
        sys.stdin = orig

    def _create_program_and_course_enrollment(self, program_uuid, user):
        program_enrollment = ProgramEnrollmentFactory(user=user, program_uuid=program_uuid)
        ProgramCourseEnrollmentFactory(program_enrollment=program_enrollment)
        return program_enrollment

    def _validate_enrollments_count(self, n):
        self.assertEqual(len(CourseEnrollment.objects.all()), n)
        self.assertEqual(len(ProgramCourseEnrollment.objects.all()), n)
        self.assertEqual(len(ProgramEnrollment.objects.all()), n)

    def test_reset(self):
        """ Validate enrollments with a user and waiting enrollments without a user are removed """
        self._create_program_and_course_enrollment(self.program_uuid, self.user)
        self._create_program_and_course_enrollment(self.program_uuid, None)

        call_command(self.command, self.program_uuid, force=True)

        self._validate_enrollments_count(0)

    def test_reset_confirmation(self):
        """ By default this command will require user input to confirm """
        self._create_program_and_course_enrollment(self.program_uuid, self.user)

        with self._replace_stdin('confirm'):
            call_command(self.command, self.program_uuid)

        self._validate_enrollments_count(0)

    def test_reset_confirmation_failure(self):
        """ Failing to confirm reset will result in no modifications """
        self._create_program_and_course_enrollment(self.program_uuid, self.user)

        with self.assertRaises(CommandError):
            with self._replace_stdin('no'):
                call_command(self.command, self.program_uuid)

        self._validate_enrollments_count(1)

    def test_reset_scope(self):
        """ reset should only affect provided programs """
        self._create_program_and_course_enrollment(self.program_uuid, self.user)

        alt_program_uuid = uuid4()
        alt_user = UserFactory()
        self._create_program_and_course_enrollment(alt_program_uuid, alt_user)

        call_command(self.command, self.program_uuid, force=True)

        # enrollment with different uuid still exists
        program_enrollment = ProgramEnrollment.objects.get(program_uuid=alt_program_uuid)
        program_course_enrollment = ProgramCourseEnrollment.objects.get(program_enrollment=program_enrollment)
        course_enrollment = program_course_enrollment.course_enrollment
        self.assertIsNotNone(course_enrollment)

        # other enrollments have been deleted
        self._validate_enrollments_count(1)

    def test_reset_multiple_programs(self):
        self._create_program_and_course_enrollment(self.program_uuid, self.user)
        alt_program_uuid = uuid4()
        alt_user = UserFactory()
        self._create_program_and_course_enrollment(alt_program_uuid, alt_user)

        call_command(self.command, '{},{}'.format(self.program_uuid, alt_program_uuid), force=True)

        self._validate_enrollments_count(0)
