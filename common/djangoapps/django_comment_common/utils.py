from django_comment_common.models import Role

_STUDENT_ROLE_PERMISSIONS = ["vote", "update_thread", "follow_thread", "unfollow_thread",
                             "update_comment", "create_sub_comment", "unvote", "create_thread",
                             "follow_commentable", "unfollow_commentable", "create_comment", ]

_MODERATOR_ROLE_PERMISSIONS = ["edit_content", "delete_thread", "openclose_thread",
                               "endorse_comment", "delete_comment", "see_all_cohorts"]

_ADMINISTRATOR_ROLE_PERMISSIONS = ["manage_moderator"]

def seed_permissions_roles(course_id):
    administrator_role = Role.objects.get_or_create(name="Administrator", course_id=course_id)[0]
    moderator_role = Role.objects.get_or_create(name="Moderator", course_id=course_id)[0]
    community_ta_role = Role.objects.get_or_create(name="Community TA", course_id=course_id)[0]
    student_role = Role.objects.get_or_create(name="Student", course_id=course_id)[0]

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


def _remove_permission_role(course_id, name):
    try:
        role = Role.objects.get(name=name, course_id=course_id)
        if role.course_id == course_id:
            role.delete()
    except Role.DoesNotExist:
        pass


def unseed_permissions_roles(course_id):
    """
    A utility method to clean up all forum related permissions and roles
    """
    _remove_permission_role(name="Administrator", course_id=course_id)
    _remove_permission_role(name="Moderator", course_id=course_id)
    _remove_permission_role(name="Community TA", course_id=course_id)
    _remove_permission_role(name="Student", course_id=course_id)


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
