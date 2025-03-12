"""
Tests for course_to_library_import validators
"""

from django.test import TestCase
import pytest

from cms.djangoapps.course_to_library_import.validators import validate_course_ids


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
