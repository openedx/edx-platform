"""
This module contains utility functions for grading.
"""


import logging
from datetime import timedelta

from django.utils import timezone
<<<<<<< HEAD
=======
from django.conf import settings
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .config.waffle import ENFORCE_FREEZE_GRADE_AFTER_COURSE_END

log = logging.getLogger(__name__)


def are_grades_frozen(course_key):
    """
    Returns whether grades are frozen for the given course.
    """
    if ENFORCE_FREEZE_GRADE_AFTER_COURSE_END.is_enabled(course_key):
        course = CourseOverview.get_from_id(course_key)
        if course.end:
<<<<<<< HEAD
            freeze_grade_date = course.end + timedelta(30)
=======
            freeze_grade_date = course.end + timedelta(settings.GRADEBOOK_FREEZE_DAYS)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            now = timezone.now()
            return now > freeze_grade_date
    return False
