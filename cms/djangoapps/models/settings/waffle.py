"""
Togglable settings for Course Grading behavior
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag


WAFFLE_NAMESPACE = 'grades'

# edx/edx-platform feature
MATERIAL_RECOMPUTE_ONLY = 'MATERIAL_RECOMPUTE_ONLY'


def material_recompute_only(course_key):
    """
    Checks to see if the CourseWaffleFlag or Django setting for material recomputer only is enabled
    """
    if CourseWaffleFlag(WAFFLE_NAMESPACE, MATERIAL_RECOMPUTE_ONLY).is_enabled(course_key):
        return True
    return False
