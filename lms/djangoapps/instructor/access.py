"""
Access control operations for use by instructor APIs.

Does not include any access control, be sure to check access before calling.

TODO sync instructor and staff flags
    e.g. should these be possible?
        {instructor: true, staff: false}
        {instructor: true, staff: true}
"""

from django.contrib.auth.models import User, Group
from courseware.access import get_access_group_name
from django_comment_common.models import (Role,
                                          FORUM_ROLE_ADMINISTRATOR,
                                          FORUM_ROLE_MODERATOR,
                                          FORUM_ROLE_COMMUNITY_TA)


def list_with_level(course, level):
    grpname = get_access_group_name(course, level)
    try:
        return Group.objects.get(name=grpname).user_set.all()
    except Group.DoesNotExist:
        return []


def allow_access(course, user, level):
    """
    Allow user access to course modification.

    level is one of ['instructor', 'staff']
    """
    _change_access(course, user, level, 'allow')


def revoke_access(course, user, level):
    """
    Revoke access from user to course modification.

    level is one of ['instructor', 'staff']
    """
    _change_access(course, user, level, 'revoke')


def _change_access(course, user, level, mode):
    """
    Change access of user.

    level is one of ['instructor', 'staff']
    mode is one of ['allow', 'revoke']
    """
    grpname = get_access_group_name(course, level)
    group, _ = Group.objects.get_or_create(name=grpname)

    if mode == 'allow':
        user.groups.add(group)
    elif mode == 'revoke':
        user.groups.remove(group)
    else:
        raise ValueError("unrecognized mode '{}'".format(mode))


def update_forum_role_membership(course_id, user, rolename, mode):
    """
    Change forum access of user.

    rolename is one of [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]

    mode is one of ['alow', 'revoke']
    """
    role = Role.objects.get(course_id=course_id, name=rolename)

    if mode == 'allow':
        role.users.add(user)
    elif mode == 'revoke':
        role.users.remove(user)
        print "\n" * 5
        print role.users.all()
    else:
        raise ValueError("unrecognized mode '{}'".format(mode))
