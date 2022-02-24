"""
Tahoe Authentication helpers for managing course related roles.
"""

from common.djangoapps.student.roles import CourseCreatorRole, OrgStaffRole


def update_organization_staff_roles(user, organization_short_name, set_as_organization_staff=False):
    """
    Update the organization-wide OrgStaffRole/CourseCreatorRole for using Studio and instructor dashboards.
    """
    assert user, 'Parameter `user` is required.'
    assert organization_short_name, 'Parameter `organization_short_name` is required.'

    organization_role = OrgStaffRole(organization_short_name)
    creator_role = CourseCreatorRole()

    if set_as_organization_staff:
        organization_role.add_users(user)
        creator_role.add_users(user)
    else:
        organization_role.remove_users(user)
        creator_role.remove_users(user)
