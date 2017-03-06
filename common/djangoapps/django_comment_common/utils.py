from django_comment_common.models import Role


class ThreadContext(object):
    """ An enumeration that represents the context of a thread. Used primarily by the comments service. """
    STANDALONE = 'standalone'
    COURSE = 'course'


_STUDENT_ROLE_PERMISSIONS = ["vote", "update_thread", "follow_thread", "unfollow_thread",
                             "update_comment", "create_sub_comment", "unvote", "create_thread",
                             "follow_commentable", "unfollow_commentable", "create_comment", ]

_MODERATOR_ROLE_PERMISSIONS = ["edit_content", "delete_thread", "openclose_thread",
                               "endorse_comment", "delete_comment", "see_all_cohorts"]

_ADMINISTRATOR_ROLE_PERMISSIONS = ["manage_moderator"]


def _save_forum_role(course_key, name):
    """
    Save and Update 'course_key' for all roles which are already created to keep course_id same
    as actual passed course key
    """
    role, created = Role.objects.get_or_create(name=name, course_id=course_key)
    if created is False:
        role.course_id = course_key
        role.save()

    return role


def seed_permissions_roles(course_key):
    """
    Create and assign permissions for forum roles
    """
    administrator_role = _save_forum_role(course_key, "Administrator")
    moderator_role = _save_forum_role(course_key, "Moderator")
    community_ta_role = _save_forum_role(course_key, "Community TA")
    student_role = _save_forum_role(course_key, "Student")

    for per in _STUDENT_ROLE_PERMISSIONS:
        student_role.add_permission(per)

    for per in _MODERATOR_ROLE_PERMISSIONS:
        moderator_role.add_permission(per)

    for per in _ADMINISTRATOR_ROLE_PERMISSIONS:
        administrator_role.add_permission(per)

    moderator_role.inherit_permissions(student_role)

    # For now, Community TA == Moderator, except for the styling.
    community_ta_role.inherit_permissions(moderator_role)

    administrator_role.inherit_permissions(moderator_role)


def are_permissions_roles_seeded(course_id):
    """
    Returns whether the forums permissions for a course have been provisioned in
    the database
    """
    try:
        administrator_role = Role.objects.get(name="Administrator", course_id=course_id)
        moderator_role = Role.objects.get(name="Moderator", course_id=course_id)
        student_role = Role.objects.get(name="Student", course_id=course_id)
    except:
        return False

    for per in _STUDENT_ROLE_PERMISSIONS:
        if not student_role.has_permission(per):
            return False

    for per in _MODERATOR_ROLE_PERMISSIONS + _STUDENT_ROLE_PERMISSIONS:
        if not moderator_role.has_permission(per):
            return False

    for per in _ADMINISTRATOR_ROLE_PERMISSIONS + _MODERATOR_ROLE_PERMISSIONS + _STUDENT_ROLE_PERMISSIONS:
        if not administrator_role.has_permission(per):
            return False

    return True
