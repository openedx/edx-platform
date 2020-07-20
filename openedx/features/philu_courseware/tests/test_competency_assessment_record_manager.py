from django.test import TestCase
from opaque_keys.edx.keys import UsageKey

from openedx.features.philu_courseware.models import CompetencyAssessmentRecord
from student.tests.factories import UserFactory

from .factories import CompetencyAssessmentRecordFactory


class CompetencyAssessmentRecordManagerTestCase(TestCase):

    def setup_attempts(self, assessment_type='post'):
        for question_number in range(5):
            CompetencyAssessmentRecordFactory(
                user=self.user,
                assessment_type=assessment_type,
                question_number=question_number + 1
            )

    def delete_post_assessment_attempts(self):
        return CompetencyAssessmentRecord.objects.revert_user_post_assessment_attempts(
            user=self.user, problem_id=self.problem_id
        )

    def setUp(self):
        self.user = UserFactory()
        self.problem_id = UsageKey.from_string(
            'block-v1:PUCIT+IT1+1+type@problem+block@7f1593ef300e4f569e26356b65d3b76b'
        )

    def test_revert_post_assessment_attempts_with_zero_attempts(self):
        """Test revert post assessment attempts method when user has not attempted any assessment"""
        deleted_attempts_count = self.delete_post_assessment_attempts()
        self.assertEqual(deleted_attempts_count, 0)

    def test_revert_post_assessment_attempts_with_pre_assessment_attempted(self):
        """Test revert post assessment attempts method when user has attempted only pre assessment"""
        self.setup_attempts('pre')
        deleted_attempts_count = self.delete_post_assessment_attempts()
        self.assertEqual(deleted_attempts_count, 0)

    def test_revert_post_assessment_attempts_with_post_assessment_attempted(self):
        """Test revert post assessment attempts method when user has attempted post assessment"""
        self.setup_attempts()
        deleted_attempts_count = self.delete_post_assessment_attempts()
        self.assertEqual(deleted_attempts_count, 5)
