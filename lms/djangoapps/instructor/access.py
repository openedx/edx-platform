"""
Access control operations for use by instructor APIs.

Does not include any access control, be sure to check access before calling.

TODO sync instructor and staff flags
    e.g. should these be possible?
        {instructor: true, staff: false}
        {instructor: true, staff: true}
"""

import logging
from django.contrib.auth.models import Group
from courseware.access import (get_access_group_name,
                               course_beta_test_group_name)
from django_comment_common.models import Role

log = logging.getLogger(__name__)


def list_with_level(course, level):
    """
    List users who have 'level' access.

    level is in ['instructor', 'staff', 'beta'] for standard courses.
    There could be other levels specific to the course.
    If there is no Group for that course-level, returns an empty list
    """
    if level == 'beta':
        grpname = course_beta_test_group_name(course.location)
    else:
        grpname = get_access_group_name(course, level)

    try:
        return Group.objects.get(name=grpname).user_set.all()
    except Group.DoesNotExist:
        log.info("list_with_level called with non-existant group named {}".format(grpname))
        return []


def allow_access(course, user, level):
    """
    Allow user access to course modification.

    level is one of ['instructor', 'staff', 'beta']
    """
    _change_access(course, user, level, 'allow')


def revoke_access(course, user, level):
    """
    Revoke access from user to course modification.

    level is one of ['instructor', 'staff', 'beta']
    """
    _change_access(course, user, level, 'revoke')


def _change_access(course, user, level, action):
    """
    Change access of user.

    level is one of ['instructor', 'staff', 'beta']
    action is one of ['allow', 'revoke']

    NOTE: will create a group if it does not yet exist.
    """

    if level == 'beta':
        grpname = course_beta_test_group_name(course.location)
    elif level in ['instructor', 'staff']:
        grpname = get_access_group_name(course, level)
    else:
        raise ValueError("unrecognized level '{}'".format(level))
    group, _ = Group.objects.get_or_create(name=grpname)

    if action == 'allow':
        user.groups.add(group)
    elif action == 'revoke':
        user.groups.remove(group)
    else:
        raise ValueError("unrecognized action '{}'".format(action))


def update_forum_role_membership(course_id, user, rolename, action):
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
