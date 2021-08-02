"""
Simple permissions for Learning Sequences.

Most access rules determining what a user will see are determined within the
outline processors themselves. This is where we'd put permissions that are used
to determine whether those processors even need to be run to filter the results.
"""
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.roles import (
    GlobalStaff,
    CourseInstructorRole,
    CourseStaffRole,
)
from openedx.core import types

from ..toggles import USE_FOR_OUTLINES


def can_call_public_api(course_key: CourseKey) -> bool:
    """
    This is only intended for rollout purposes, and eventually everyone will be
    able to call the public API for all courses.
    """
    return USE_FOR_OUTLINES.is_enabled(course_key)


def can_see_all_content(requesting_user: types.User, course_key: CourseKey) -> bool:
    """
    Global staff, course staff, and instructors can see everything.

    There's no need to run processors to restrict results for these users.
    """
    return (
        GlobalStaff().has_user(requesting_user) or
        CourseStaffRole(course_key).has_user(requesting_user) or
        CourseInstructorRole(course_key).has_user(requesting_user)
    )


def can_see_content_as_other_users(requesting_user: types.User, course_key: CourseKey) -> bool:
    """
    Is this user allowed to view this content as other users?

    For now, this is the same set of people who are allowed to see all content
    (i.e. some kind of course or global staff). It's possible that we'll want to
    make more granular distinctions between different kinds of staff roles in
    the future (e.g. CourseDataResearcher).
    """
    return can_see_all_content(requesting_user, course_key)
