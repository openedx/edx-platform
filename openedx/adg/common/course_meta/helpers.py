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
        Course short id, starting from 100
    """
    next_short_id = 100  # Start with smallest three digit id
    CourseMeta = apps.get_model('course_meta', 'CourseMeta')  # noqa

    with suppress(OperationalError):
        latest_db_entry = CourseMeta.objects.last()
        if latest_db_entry:
            next_short_id += latest_db_entry.id

    return next_short_id
