"""
Simple permissions for Learning Sequences.

Most access rules determining what a user will see are determined within the
outline processors themselves. This is where we'd put permissions that are used
to determine whether those processors even need to be run to filter the results.
"""
from opaque_keys.edx.keys import CourseKey
from django.contrib.auth import User

from common.djangoapps.student.roles import (
    GlobalStaff,
    CourseInstructorRole,
    CourseStaffRole,
)
from lms.djangoapps.courseware.access import has_access

from ..toggles import USE_FOR_OUTLINES


def can_call_public_api(requesting_user: User, course_key: CourseKey) -> bool:
    """
    Global staff can always call the public API. Otherwise, check waffle flag.

    This is only intended for rollout purposes, and eventually everyone will be
    able to call the public API for all courses.
    """
    return GlobalStaff().has_user(requesting_user) or USE_FOR_OUTLINES.is_enabled(course_key)


def can_see_all_content(requesting_user: User, course_key: CourseKey) -> bool:
    """
    Global staff, course staff, and instructors can see everything.

    There's no need to run processors to restrict results for these users.
    """
    return (
        GlobalStaff().has_user(requesting_user) or
        CourseStaffRole(course_key).has_user(requesting_user) or
        CourseInstructorRole(course_key).has_user(requesting_user)
    )


def can_see_user_course_outline(requesting_user: User, target_user: User, course_key: CourseKey) -> bool:
    """
    Returns whether the requesting_user can access the outline of a target_user
    for a given course.
    """
    # Obviously, a user can see their own outline.
    if requesting_user.id == target_user.id:
        return True
    # Otherwise, one must be course staff to see users' outlines.
    has_access(requesting_user, CourseStaffRole.ROLE, course_key)
