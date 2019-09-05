"""
Tests for account linking Python API.
"""
from __future__ import absolute_import, unicode_literals

from uuid import UUID

from django.test import TestCase

from lms.djangoapps.program_enrollments.constants import ProgramEnrollmentStatuses as PEStatuses
from lms.djangoapps.program_enrollments.tests.factories import ProgramEnrollmentFactory

from ..reading import fetch_program_enrollments


class TestProgramEnrollmentReading(TestCase):
    """
    Tests for program enrollment reading functions.

    TODO: This currently only tests fetch_program_enrollments by
    external_user_key.
    """
    program_uuid_1 = UUID('7aeadb7d-5f48-493d-9410-84e1d36c657f')
    program_uuid_2 = UUID('b08071d8-f803-43f6-bbf3-5ae15d393649')
    curriculum_uuid_a = UUID('e331472e-bd26-43d0-94b8-b0063858210b')
    curriculum_uuid_b = UUID('db717f6c-145f-43db-ad05-f9ad65eec285')

    def test_fetch_by_student_key(self):
        user_keys = set()
        test_data = [
            (self.program_uuid_1, self.curriculum_uuid_a, PEStatuses.ENROLLED),
            (self.program_uuid_1, self.curriculum_uuid_b, PEStatuses.PENDING),
            (self.program_uuid_1, self.curriculum_uuid_a, PEStatuses.ENROLLED),
            (self.program_uuid_1, self.curriculum_uuid_b, PEStatuses.PENDING),
            (self.program_uuid_2, self.curriculum_uuid_a, PEStatuses.ENROLLED),
        ]
        for i, (program_uuid, curriculum_uuid, status) in enumerate(test_data):
            user_key = 'student-{}'.format(i)
            ProgramEnrollmentFactory(
                user=None,
                external_user_key=user_key,
                program_uuid=program_uuid,
                curriculum_uuid=curriculum_uuid,
                status=status,
            )
            user_keys.add(user_key)
        actual_enrollments = fetch_program_enrollments(
            program_uuid=self.program_uuid_1,
            external_user_keys=user_keys,
        )
        expected_enrollments = {
            'student-0': {
                'curriculum_uuid': self.curriculum_uuid_a,
                'status': 'enrolled',
                'program_uuid': self.program_uuid_1,
            },
            'student-1': {
                'curriculum_uuid': self.curriculum_uuid_b,
                'status': 'pending',
                'program_uuid': self.program_uuid_1,
            },
            'student-2': {
                'curriculum_uuid': self.curriculum_uuid_a,
                'status': 'enrolled',
                'program_uuid': self.program_uuid_1,
            },
            'student-3': {
                'curriculum_uuid': self.curriculum_uuid_b,
                'status': 'pending',
                'program_uuid': self.program_uuid_1,
            },
        }
        assert expected_enrollments == {
            enrollment.external_user_key: {
                'curriculum_uuid': enrollment.curriculum_uuid,
                'status': enrollment.status,
                'program_uuid': enrollment.program_uuid,
            }
            for enrollment in actual_enrollments
        }
