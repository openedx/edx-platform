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
        self.enrollment = ProgramEnrollment.objects.create(
            user=self.user,
            external_user_key='abc',
            program_uuid=uuid4(),
            curriculum_uuid=uuid4(),
            status='enrolled'
        )

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
