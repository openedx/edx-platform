"""
Togglable settings for Course Grading behavior
"""
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_NAMESPACE = 'grades'

# edx/edx-platform feature
MATERIAL_RECOMPUTE_ONLY = 'MATERIAL_RECOMPUTE_ONLY'

MATERIAL_RECOMPUTE_ONLY_FLAG = CourseWaffleFlag(
    waffle_namespace=WAFFLE_NAMESPACE,
    flag_name=MATERIAL_RECOMPUTE_ONLY,
    module_name=__name__,
)


def material_recompute_only(course_key):
    """
    Checks to see if the CourseWaffleFlag or Django setting for material recomputer only is enabled
    """
    if MATERIAL_RECOMPUTE_ONLY_FLAG.is_enabled(course_key):
        return True
    return False
