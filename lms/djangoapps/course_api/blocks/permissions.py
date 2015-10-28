"""
Encapsulates permissions checks for Course Blocks API
"""

from courseware.access import has_access
from student.models import CourseEnrollment


def can_access_other_users_blocks(requesting_user, course_key):
    """
    Returns whether the requesting_user can access the blocks for
    other users in the given course.
    """
    return has_access(requesting_user, 'staff', course_key)


def can_access_users_blocks(requested_user, course_key):
    """
    Returns whether blocks for the requested_user is accessible.
    """
    return (
        (requested_user.id and CourseEnrollment.is_enrolled(requested_user, course_key)) or
        has_access(requested_user, 'staff', course_key)
    )
