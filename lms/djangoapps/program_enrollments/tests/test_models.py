"""
Unit tests for ProgramEnrollment models.
"""
from __future__ import absolute_import, unicode_literals

from uuid import uuid4

from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from six.moves import range
from testfixtures import LogCapture

from lms.djangoapps.program_enrollments.models import ProgramCourseEnrollment, ProgramEnrollment
from openedx.core.djangoapps.catalog.tests.factories import generate_course_run_key
from student.tests.factories import CourseEnrollmentFactory, UserFactory


class ProgramEnrollmentModelTests(TestCase):
    """
    Tests for the ProgramEnrollment model.
    """
    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(ProgramEnrollmentModelTests, self).setUp()
        self.user = UserFactory.create()
        self.program_uuid = uuid4()
        self.other_program_uuid = uuid4()
        self.enrollment = ProgramEnrollment.objects.create(
            user=self.user,
            external_user_key='abc',
            program_uuid=self.program_uuid,
            curriculum_uuid=uuid4(),
            status='enrolled'
        )

    def test_bulk_read_by_student_key(self):
        curriculum_a = uuid4()
        curriculum_b = uuid4()
        enrollments = []
        student_data = {}

        for i in range(5):
            # This will give us 4 program enrollments for self.program_uuid
            # and 1 enrollment for self.other_program_uuid
            user_curriculum = curriculum_b if i % 2 else curriculum_a
            user_status = 'pending' if i % 2 else 'enrolled'
            user_program = self.other_program_uuid if i == 4 else self.program_uuid
            user_key = 'student-{}'.format(i)
            enrollments.append(
                ProgramEnrollment.objects.create(
                    user=None,
                    external_user_key=user_key,
                    program_uuid=user_program,
                    curriculum_uuid=user_curriculum,
                    status=user_status,
                )
            )
            student_data[user_key] = {'curriculum_uuid': user_curriculum}

        enrollment_records = ProgramEnrollment.bulk_read_by_student_key(self.program_uuid, student_data)

        expected = {
            'student-0': {'curriculum_uuid': curriculum_a, 'status': 'enrolled', 'program_uuid': self.program_uuid},
            'student-1': {'curriculum_uuid': curriculum_b, 'status': 'pending', 'program_uuid': self.program_uuid},
            'student-2': {'curriculum_uuid': curriculum_a, 'status': 'enrolled', 'program_uuid': self.program_uuid},
            'student-3': {'curriculum_uuid': curriculum_b, 'status': 'pending', 'program_uuid': self.program_uuid},
        }
        assert expected == {
            enrollment.external_user_key: {
                'curriculum_uuid': enrollment.curriculum_uuid,
                'status': enrollment.status,
                'program_uuid': enrollment.program_uuid,
            }
            for enrollment in enrollment_records
        }

    def test_user_retirement(self):
        """
        Test that the external_user_key is successfully retired for a user's program enrollments and history.
        """
        new_status = 'withdrawn'

        self.enrollment.status = new_status
        self.enrollment.save()

        # Ensure that all the records had values for external_user_key
        self.assertEquals(self.enrollment.external_user_key, 'abc')

        self.assertTrue(self.enrollment.historical_records.all())
        for record in self.enrollment.historical_records.all():
            self.assertEquals(record.external_user_key, 'abc')

        ProgramEnrollment.retire_user(self.user.id)
        self.enrollment.refresh_from_db()

        # Ensure those values are retired
        self.assertEquals(self.enrollment.external_user_key, None)

        self.assertTrue(self.enrollment.historical_records.all())
        for record in self.enrollment.historical_records.all():
            self.assertEquals(record.external_user_key, None)


class ProgramCourseEnrollmentModelTests(TestCase):
    """
    Tests for the ProgramCourseEnrollment model.
    """
    def setUp(self):
        """
        Set up test data
        """
        super(ProgramCourseEnrollmentModelTests, self).setUp()
        self.user = UserFactory.create()
        self.program_uuid = uuid4()
        self.program_enrollment = ProgramEnrollment.objects.create(
            user=self.user,
            external_user_key='abc',
            program_uuid=self.program_uuid,
            curriculum_uuid=uuid4(),
            status='enrolled'
        )
        self.course_key = CourseKey.from_string(generate_course_run_key())
        self.course_enrollment = CourseEnrollmentFactory.create(
            course_id=self.course_key,
            user=self.user,
        )
        self.program_course_enrollment = ProgramCourseEnrollment.objects.create(
            program_enrollment=self.program_enrollment,
            course_key=self.course_key,
            course_enrollment=self.course_enrollment,
            status="active"
        )

    def test_change_status_no_enrollment(self):
        with LogCapture() as capture:
            self.program_course_enrollment.course_enrollment = None
            self.program_course_enrollment.change_status("inactive")
            expected_message = "User {} {} {} has no course_enrollment".format(
                self.user,
                self.program_enrollment,
                self.course_key
            )
            capture.check(
                ('lms.djangoapps.program_enrollments.models', 'WARNING', expected_message)
            )

    def test_change_status_not_active_or_inactive(self):
        with LogCapture() as capture:
            status = "potential-future-status-0123"
            self.program_course_enrollment.change_status(status)
            message = ("Changed {} status to {}, not changing course_enrollment"
                       " status because status is not 'active' or 'inactive'")
            expected_message = message.format(self.program_course_enrollment, status)
            capture.check(
                ('lms.djangoapps.program_enrollments.models', 'WARNING', expected_message)
            )
