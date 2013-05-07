from django_comment_common.models import Role


def seed_permissions_roles(course_id):
    administrator_role = Role.objects.get_or_create(name="Administrator", course_id=course_id)[0]
    moderator_role = Role.objects.get_or_create(name="Moderator", course_id=course_id)[0]
    community_ta_role = Role.objects.get_or_create(name="Community TA", course_id=course_id)[0]
    student_role = Role.objects.get_or_create(name="Student", course_id=course_id)[0]

    for per in ["vote", "update_thread", "follow_thread", "unfollow_thread",
                "update_comment", "create_sub_comment", "unvote", "create_thread",
                "follow_commentable", "unfollow_commentable", "create_comment", ]:
        student_role.add_permission(per)

    for per in ["edit_content", "delete_thread", "openclose_thread",
                "endorse_comment", "delete_comment", "see_all_cohorts"]:
        moderator_role.add_permission(per)

    for per in ["manage_moderator"]:
        administrator_role.add_permission(per)

    moderator_role.inherit_permissions(student_role)

    # For now, Community TA == Moderator, except for the styling.
    community_ta_role.inherit_permissions(moderator_role)

    administrator_role.inherit_permissions(moderator_role)


def are_permissions_roles_seeded(course_id):

    try:
        administrator_role = Role.objects.get(name="Administrator", course_id=course_id)
        moderator_role = Role.objects.get(name="Moderator", course_id=course_id)
        student_role = Role.objects.get(name="Student", course_id=course_id)
    except:
        return False

    for per in ["vote", "update_thread", "follow_thread", "unfollow_thread",
                "update_comment", "create_sub_comment", "unvote", "create_thread",
                "follow_commentable", "unfollow_commentable", "create_comment", ]:
        if not student_role.has_permission(per):
            return False

    for per in ["edit_content", "delete_thread", "openclose_thread",
                "endorse_comment", "delete_comment", "see_all_cohorts"]:
        if not moderator_role.has_permission(per):
            return False

    for per in ["manage_moderator"]:
        if not administrator_role.has_permission(per):
            return False

    return True