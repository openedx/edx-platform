"""
Tests for course_to_library_import validators
"""

from typing import get_args
from unittest.mock import MagicMock

from django.test import TestCase
import pytest

from cms.djangoapps.course_to_library_import.validators import (
    validate_course_ids,
    validate_usage_ids,
    validate_composition_level
)
from cms.djangoapps.course_to_library_import.types import CompositionLevel


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


class TestValidateUsageIds(TestCase):
    """
    Test cases for validate_usage_ids function.

    Case 1: Valid usage ids
    Case 2: Invalid usage ids
    """

    def test_valid_usage_ids(self):
        staged_content = MagicMock()
        staged_content.values_list.return_value = [
            ['block-v1:edX+DemoX+type@problem+block@12345'],
            ['block-v1:edX+DemoX+type@video+block@67890'],
        ]
        validate_usage_ids(['block-v1:edX+DemoX+type@problem+block@12345'], staged_content)

    def test_invalid_usage_ids(self):
        staged_content = MagicMock()
        staged_content.values_list.return_value = [
            ['block-v1:edX+DemoX+type@problem+block@12345'],
            ['block-v1:edX+DemoX+type@video+block@67890'],
        ]
        with pytest.raises(ValueError) as exc:
            validate_usage_ids(['block-v1:edX+DemoX+type@discussion+block@54321'], staged_content)
            assert str(exc.value) == 'Block block-v1:edX+DemoX+type@discussion+block@54321 is not available for import'


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
