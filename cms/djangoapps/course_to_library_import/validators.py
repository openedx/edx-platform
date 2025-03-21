"""
Validators for the course_to_library_import app.
"""

from collections import ChainMap
from typing import get_args

from django.utils.translation import gettext_lazy as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .types import CompositionLevel


def validate_course_ids(value: str):
    """
    Validate that the course_ids are valid course keys.

    Args:
        value (str): A string containing course IDs separated by spaces.

    Raises:
        ValueError: If the course IDs are not valid course keys or if there are duplicate course keys.
    """

    course_ids = value.split()
    if len(course_ids) != len(set(course_ids)):
        raise ValueError(_('Duplicate course keys are not allowed'))

    for course_id in course_ids:
        try:
            CourseKey.from_string(course_id)
        except InvalidKeyError as exc:
            raise ValueError(_('Invalid course key: {course_id}').format(course_id=course_id)) from exc


def validate_usage_ids(usage_ids, staged_content):
    available_block_keys = ChainMap(*staged_content.values_list('tags', flat=True))
    for usage_key in usage_ids:
        if usage_key not in available_block_keys:
            raise ValueError(f'Block {usage_key} is not available for import')


def validate_composition_level(composition_level):
    if composition_level not in get_args(CompositionLevel):
        raise ValueError(
            _('Invalid composition level: {composition_level}').format(composition_level=composition_level)
        )
