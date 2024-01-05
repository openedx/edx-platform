"""
Helpers for student roles
"""


from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR,
    Role
)
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.lib.cache_utils import request_cached
from common.djangoapps.student.roles import (
    CourseBetaTesterRole,
    CourseInstructorRole,
    CourseStaffRole,
    GlobalStaff,
    OrgInstructorRole,
    OrgStaffRole
)


@request_cached()
def has_staff_roles(user, course_key):
    """
    Return true if a user has any of the following roles
    Staff, Instructor, Beta Tester, Forum Community TA, Forum Group Moderator, Forum Moderator, Forum Administrator
    """
    # TODO: remove role checks once course_roles is fully implemented and data is migrated
    forum_roles = [FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_GROUP_MODERATOR,
                   FORUM_ROLE_MODERATOR, FORUM_ROLE_ADMINISTRATOR]
    permissions = [
        CourseRolesPermission.MODERATE_DISCUSSION_FORUMS.value,
        CourseRolesPermission.MODERATE_DISCUSSION_FORUMS_FOR_A_COHORT.value,
    ]
    is_staff = CourseStaffRole(course_key).has_user(user)
    is_instructor = CourseInstructorRole(course_key).has_user(user)
    is_beta_tester = CourseBetaTesterRole(course_key).has_user(user)
    is_org_staff = OrgStaffRole(course_key.org).has_user(user)
    is_org_instructor = OrgInstructorRole(course_key.org).has_user(user)
    is_global_staff = GlobalStaff().has_user(user)
    has_forum_role = Role.user_has_role_for_course(user, course_key, forum_roles)
    has_discussion_perms = any(user.has_perm(permission, course_key) for permission in permissions)
    if (
        any([is_staff, is_instructor, is_beta_tester, is_org_staff,
            is_org_instructor, is_global_staff, has_forum_role, has_discussion_perms])
    ):
        return True
    return False
