"""
Common utils for the `course_info` API.
"""

import logging
from typing import List, Optional, Union

from django.core.cache import cache

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.core.djangoapps.content.block_structure.api import get_block_structure_manager

log = logging.getLogger(__name__)


def calculate_progress(
    user: 'User',  # noqa: F821
    course_id: 'CourseLocator',  # noqa: F821
    cache_timeout: int,
) -> Optional[List[Union['ReadSubsectionGrade', 'ZeroSubsectionGrade']]]:  # noqa: F821
    """
    Calculate the progress of the user in the course.
    """
    is_staff = bool(has_access(user, 'staff', course_id))

    try:
        cache_key = f'course_block_structure_{str(course_id)}_{user.id}'
        collected_block_structure = cache.get(cache_key)
        if not collected_block_structure:
            collected_block_structure = get_block_structure_manager(course_id).get_collected()
            cache.set(cache_key, collected_block_structure, cache_timeout)

        course_grade = CourseGradeFactory().read(user, collected_block_structure=collected_block_structure)

        # recalculate course grade from visible grades (stored grade was calculated over all grades, visible or not)
        course_grade.update(visible_grades_only=True, has_staff_access=is_staff)
        subsection_grades = list(course_grade.subsection_grades.values())
    except Exception as err:  # pylint: disable=broad-except
        log.warning(f'Could not get grades for the course: {course_id}, error: {err}')
        return []

    return subsection_grades
