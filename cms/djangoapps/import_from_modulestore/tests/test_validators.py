"""
Tests for import_from_modulestore validators
"""

from typing import get_args

from django.test import TestCase
import pytest

from cms.djangoapps.import_from_modulestore.validators import (
    validate_course_ids,
    validate_composition_level,
)
from cms.djangoapps.import_from_modulestore.types import CompositionLevel


class TestValidateCourseIds(TestCase):
    """
    Test cases for validate_course_ids function.

    Case 1: Valid course ids
    Case 2: Invalid course ids
    Case 3: Duplicate course ids
    """

    def test_valid_course_ids(self):
        validate_course_ids('course-v1:edX+DemoX+Demo_Course course-v1:edX+DemoX+Demo_Course2')

    def test_invalid_course_ids(self):
        with pytest.raises(ValueError) as exc:
            validate_course_ids('course-v1:edX+DemoX+Demo_Course invalid_course_id')
            assert str(exc.value) == 'Invalid course key: invalid_course_id'

    def test_duplicate_course_ids(self):
        with pytest.raises(ValueError) as exc:
            validate_course_ids('course-v1:edX+DemoX+Demo_Course course-v1:edX+DemoX+Demo_Course')
        assert str(exc.value) == 'Duplicate course keys are not allowed'


class TestValidateCompositionLevel(TestCase):
    """
    Test cases for validate_composition_level function.

    Case 1: Valid composition level
    Case 2: Invalid composition level
    """

    def test_valid_composition_level(self):
        for level in get_args(CompositionLevel):
            # Should not raise an exception for valid levels
            validate_composition_level(level)

    def test_invalid_composition_level(self):
        with pytest.raises(ValueError) as exc:
            validate_composition_level('invalid_composition_level')
        assert 'Invalid composition level: invalid_composition_level' in str(exc.value)
