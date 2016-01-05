"""
Encapsulates permissions checks for Course Blocks API
"""

from courseware.access import has_access
from student.models import CourseEnrollment
from student.roles import CourseStaffRole


def can_access_all_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access all the blocks
    in the course.
    """
    return has_access(requesting_user, CourseStaffRole.ROLE, course_key)


def can_access_others_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access the blocks for
    other users in the given course.
    """
    return has_access(requesting_user, CourseStaffRole.ROLE, course_key)


def can_access_self_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access own blocks.
    """
    return (
        (requesting_user.id and CourseEnrollment.is_enrolled(requesting_user, course_key)) or
        has_access(requesting_user, CourseStaffRole.ROLE, course_key)
    )
