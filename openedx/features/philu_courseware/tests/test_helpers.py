from django.test import TestCase
from rest_framework.exceptions import ValidationError

from openedx.features.philu_courseware.helpers import validate_problem_id


class ValidateProblemIdTestCase(TestCase):

    def test_empty_problem_id(self):
        """Test empty problem id"""
        with self.assertRaises(ValidationError):
            validate_problem_id('')

    def test_invalid_problem_id(self):
        """Test invalid problem id"""
        with self.assertRaises(ValidationError):
            validate_problem_id('invalid-problem-id')

    def test_valid_problem_id(self):
        """Test valid problem id"""
        try:
            validate_problem_id('block-v1:PUCIT+IT1+1+type@problem+block@7f1593ef300e4f569e26356b65d3b76b')
        except ValidationError:
            self.fail('Validation error raised for a valid problem id')
