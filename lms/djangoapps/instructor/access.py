"""
Access control operations for use by instructor APIs.

Does not include any access control, be sure to check access before calling.

TO DO sync instructor and staff flags
    e.g. should these be possible?
        {instructor: true, staff: false}
        {instructor: true, staff: true}
"""

import logging
from django_comment_common.models import Role

from student.roles import (
    CourseBetaTesterRole,
    CourseInstructorRole,
    CourseCcxCoachRole,
    CourseStaffRole,
)


log = logging.getLogger(__name__)

ROLES = {
    'beta': CourseBetaTesterRole,
    'instructor': CourseInstructorRole,
    'staff': CourseStaffRole,
    'ccx_coach': CourseCcxCoachRole,
}


def list_with_level(course, level):
    """
    List users who have 'level' access.

    `level` is in ['instructor', 'staff', 'beta'] for standard courses.
    There could be other levels specific to the course.
    If there is no Group for that course-level, returns an empty list
    """
    return ROLES[level](course.id).users_with_role()


def allow_access(course, user, level):
    """
    Allow user access to course modification.

    `level` is one of ['instructor', 'staff', 'beta']
    """
    _change_access(course, user, level, 'allow')


def revoke_access(course, user, level):
    """
    Revoke access from user to course modification.

    `level` is one of ['instructor', 'staff', 'beta']
    """
    _change_access(course, user, level, 'revoke')


def _change_access(course, user, level, action):
    """
    Change access of user.

    `level` is one of ['instructor', 'staff', 'beta']
    action is one of ['allow', 'revoke']

    NOTE: will create a group if it does not yet exist.
    """

    try:
        role = ROLES[level](course.id)
    except KeyError:
        raise ValueError("unrecognized level '{}'".format(level))

    if action == 'allow':
        role.add_users(user)
    elif action == 'revoke':
        role.remove_users(user)
    else:
        raise ValueError("unrecognized action '{}'".format(action))


def update_forum_role(course_id, user, rolename, action):
    """
    Change forum access of user.

    `rolename` is one of [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
    `action` is one of ['allow', 'revoke']

    if `action` is bad, raises ValueError
    if `rolename` does not exist, raises Role.DoesNotExist
    """
    role = Role.objects.get(course_id=course_id, name=rolename)

    if action == 'allow':
        role.users.add(user)
    elif action == 'revoke':
        role.users.remove(user)
    else:
        raise ValueError("unrecognized action '{}'".format(action))
