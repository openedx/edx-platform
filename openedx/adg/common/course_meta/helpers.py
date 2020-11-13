"""
All the helper methods for course meta app
"""
from contextlib import suppress

from django.apps import apps
from django.db.utils import OperationalError


def next_course_short_id():
    """
    Create next unique course short id. Course short id's start with three digits i.e. 100
    Returns:
        Course short if, starting from 100
    """
    course_short_id = 100  # Start with (smallest) three digit id
    CourseMeta = apps.get_model('course_meta', 'CourseMeta')  # noqa (N807), camelcase name is good for searchability

    with suppress(OperationalError):
        latest_db_entry = CourseMeta.objects.last()
        if latest_db_entry:
            course_short_id = latest_db_entry.id + course_short_id

    return course_short_id
