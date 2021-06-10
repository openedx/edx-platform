"""
Simple permissions for Learning Sequences.

Most access rules determining what as user will see are determined within the
outline processors themselves. This is where we'd put permissions that are used
to determine whether those processors even need to be run to filter the results.
"""
from common.djangoapps.student.roles import (
    GlobalStaff,
    CourseInstructorRole,
    CourseStaffRole,
)

from ..toggles import USE_FOR_OUTLINES


def can_see_all_content(requesting_user, course_key):
    """
    Global staff, course staff, and instructors can see everything.

    There's no need to run processors to restrict results for these users.
    """
    return (
        GlobalStaff().has_user(requesting_user) or
        CourseStaffRole(course_key).has_user(requesting_user) or
        CourseInstructorRole(course_key).has_user(requesting_user)
    )

def can_call_public_api(requesting_user, course_key):
    """
    Does this user have permission to see an outline for this Course Key?

    Eventually, everyone will be able to call the public outline endpoint,
    even unauthenticated users. This is just a temporary measure to gate access
    while we do waffle-controlled rollout of this feature.

    This function should not be called by the learning_sequences API itself. If
    you're calling the learning_sequences API directly from a different app
    because the bits you need are already fully implemented, this function never
    needs to be invoked. This is here to help us roll out the REST API as a
    whole.
    """
    return GlobalStaff().has_user(requesting_user) or USE_FOR_OUTLINES.is_enabled(course_key)
