"""
Unit tests for ProgramEnrollment serializers.
"""
from __future__ import absolute_import, unicode_literals

from uuid import uuid4

from django.test import TestCase

from lms.djangoapps.program_enrollments.api.v1.serializers import ProgramEnrollmentSerializer
from lms.djangoapps.program_enrollments.models import ProgramEnrollment
from student.tests.factories import UserFactory


class ProgramEnrollmentSerializerTests(TestCase):
    """
    Tests for the ProgramEnrollment serializer.
    """
    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(ProgramEnrollmentSerializerTests, self).setUp()
        self.user = UserFactory.create()
        self.enrollment = ProgramEnrollment.objects.create(
            user=self.user,
            external_user_key='abc',
            program_uuid=uuid4(),
            curriculum_uuid=uuid4(),
            status='enrolled'
        )
        self.serializer = ProgramEnrollmentSerializer(instance=self.enrollment)

    def test_serializer_contains_expected_fields(self):
        data = self.serializer.data

        self.assertEqual(
            set(data.keys()),
            set([
                'user',
                'external_user_key',
                'program_uuid',
                'curriculum_uuid',
                'status'
            ])
        )
