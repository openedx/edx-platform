"""
Unit tests for ProgramEnrollment models.
"""
from __future__ import unicode_literals

from uuid import uuid4

from django.test import TestCase

from lms.djangoapps.program_enrollments.models import ProgramEnrollment
from student.tests.factories import UserFactory


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

        for i in xrange(5):
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
        Test that the external_user_key is uccessfully retired for a user's program enrollments and history.
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
