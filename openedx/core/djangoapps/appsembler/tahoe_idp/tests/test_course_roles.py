"""
Tahoe Authentication helpers for managing Studio roles.
"""
import pytest

from common.djangoapps.student.roles import CourseCreatorRole, OrgStaffRole

from student.tests.factories import UserFactory

from openedx.core.djangoapps.appsembler.tahoe_idp import course_roles


@pytest.mark.django_db
def test_update_organization_staff_roles():
    """
    Tests for the `update_organization_staff_roles` helper.
    """
    user = UserFactory.create()
    organization_short_name = 'test-university'
    org_role = OrgStaffRole(organization_short_name)
    creator_role = CourseCreatorRole()

    assert not org_role.has_user(user), 'Sanity check: Should not include any user by default'
    assert not creator_role.has_user(user), 'Sanity check: Should not include any user by default'

    course_roles.update_organization_staff_roles(
        user=user,
        organization_short_name=organization_short_name,
        set_as_organization_staff=True,
    )

    assert org_role.has_user(user), 'Should set user as organization staff'
    assert creator_role.has_user(user), 'Should set user as Course creator'

    course_roles.update_organization_staff_roles(
        user=user,
        organization_short_name=organization_short_name,
        set_as_organization_staff=True,
    )

    assert org_role.has_user(user), 'Calling the helper twice should keep the user in the role'
    assert creator_role.has_user(user), 'Calling the helper twice should keep the user in the role'

    course_roles.update_organization_staff_roles(
        user=user,
        organization_short_name=organization_short_name,
        set_as_organization_staff=False,
    )

    assert not org_role.has_user(user), 'The helper should be able to remove the user from org staff'
    assert not creator_role.has_user(user), 'The helper should be able to remove the user from the course creators'


@pytest.mark.django_db
def test_null_parameters_to_update_organization_staff_roles():
    """
    Ensure parameter validation in the update_organization_staff_roles helper.
    """
    user = UserFactory.create()
    organization_short_name = 'test-university'

    with pytest.raises(AssertionError, match='user'):
        course_roles.update_organization_staff_roles(
            user=None,
            organization_short_name=organization_short_name,
        )

    with pytest.raises(AssertionError, match='organization_short_name'):
        course_roles.update_organization_staff_roles(
            user=user,
            organization_short_name=None,
        )
