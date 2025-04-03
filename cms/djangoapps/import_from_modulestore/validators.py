"""
Validators for the import_from_modulestore app.
"""
from django.utils.translation import gettext_lazy as _
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from .data import CompositionLevel


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


def validate_composition_level(composition_level):
    if composition_level not in CompositionLevel.values():
        raise ValueError(
            _('Invalid composition level: {composition_level}').format(composition_level=composition_level)
        )
