"""
Tahoe Authentication helpers for managing course related roles.
"""

from common.djangoapps.student.roles import (
    CourseCreatorRole,
    OrgRole,
    OrgStaffRole,
    register_access_role,
)


def update_organization_staff_roles(
    user,
    organization_short_name,
    set_as_course_author=False,
    set_as_organization_staff=False,
):
    """
    Update the organization-wide OrgStaffRole/CourseCreatorRole for using Studio and instructor dashboards.
    """
    assert user, 'Parameter `user` is required.'
    assert organization_short_name, 'Parameter `organization_short_name` is required.'

    organization_role = OrgStaffRole(organization_short_name)
    course_author_role = TahoeCourseAuthorRole(organization_short_name)
    creator_role = CourseCreatorRole()

    if set_as_organization_staff or set_as_course_author:
        # Both org-wide staff and limited course author can create courses.
        creator_role.add_users(user)
    else:
        creator_role.remove_users(user)

    if set_as_organization_staff:
        organization_role.add_users(user)
    else:
        organization_role.remove_users(user)

    if set_as_course_author:
        course_author_role.add_users(user)
    else:
        course_author_role.remove_users(user)


@register_access_role
class TahoeCourseAuthorRole(OrgRole):
    """
    A limited course access role to allow Studio access without having a course.

    A user with this role needs to be explicitly invited to a course.
    """
    ROLE = 'tahoe_course_author'

    def __init__(self, *args, **kwargs):
        super().__init__(self.ROLE, *args, **kwargs)
