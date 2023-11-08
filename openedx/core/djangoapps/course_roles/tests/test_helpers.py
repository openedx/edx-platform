"""
Tests of the course_roles.helpers module
"""
import ddt
from organizations.tests.factories import OrganizationFactory
import pytest

from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.djangoapps.course_roles.helpers import (
    user_has_permission_course_org,
    user_has_permission_list_course_org,
    user_has_permission_course,
    user_has_permission_list_course,
    user_has_permission_list_any_course,
    user_has_permission_org,
    user_has_permission_list_org,
    get_all_user_permissions_for_a_course,
    USE_PERMISSION_CHECKS_FLAG
)
from openedx.core.djangoapps.course_roles.models import (
    CourseRolesPermission,
    CourseRolesRole,
    CourseRolesService,
    CourseRolesUserRole
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=True)
class PermissionCheckTestCase(SharedModuleStoreTestCase):
    """
    Tests of the permission check functions in course_roles.helpers module
    """
    def setUp(self):
        super().setUp()
        self.user_1 = UserFactory(username="test_user_1")
        self.organization_1 = OrganizationFactory(name="test_organization_1")
        self.organization_2 = OrganizationFactory(name="test_organization_2")
        self.course_1 = CourseFactory.create(
            display_name="test course 1", run="Testing_course_1", org=self.organization_1.name
        )
        self.course_2 = CourseFactory.create(
            display_name="test course 2", run="Testing_course_2", org=self.organization_1.name
        )
        self.role_1 = CourseRolesRole.objects.create(name="test_role_1")
        self.service = CourseRolesService.objects.create(name="test_service")
        self.role_1.services.add(self.service)
        self.permission_1 = CourseRolesPermission.objects.create(name="test_permission_1")
        self.role_1.permissions.add(self.permission_1)
        self.role_2 = CourseRolesRole.objects.create(name="test_role_3")
        self.role_2.services.add(self.service)
        self.role_2.permissions.add(self.permission_1)
        self.permission_2 = CourseRolesPermission.objects.create(name="test_permission_2")
        self.role_2.permissions.add(self.permission_2)

    def test_user_has_permission_course_with_anonymus_user(self):
        """
        Test that user_has_permission_course returns False when the user is anonymous
        """
        assert not user_has_permission_course(self.anonymous_user, self.permission_1.name, self.course_1.id)

    def test_user_has_permission_course_with_course_level_permission(self):
        """
        Test that user_has_permission_course returns True when the user has the correct permission at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert user_has_permission_course(self.user_1, self.permission_1.name, self.course_1.id)

    def test_user_has_permission_course_without_course_level_permission(self):
        """
        Test that user_has_permission_course returns False when the user does not have the correct permission at the
        course level
        """
        assert not user_has_permission_course(self.user_1, self.permission_1.name, self.course_1.id)

    def test_course_permision_check_with_organization_level_permission(self):
        """
        Test that user_has_permission_course returns False when the user has the permission but at the organization
        level, and has not been granted the permission at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert not user_has_permission_course(self.user_1, self.permission_1.name, self.course_1.id)

    def test_user_has_permission_course_with_instance_level_permission(self):
        """
        Test that user_has_permission_course returns False when the user has the permission but at the instance level,
        and has not been granted the permission at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1)
        assert not user_has_permission_course(self.user_1, self.permission_1.name, self.course_1.id)

    def test_user_has_permission_course_with_permission_in_another_course(self):
        """
        Test that user_has_permission_course returns False when the user has the permission at the course level,
        but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_2.id, org=self.organization_1
        )
        assert not user_has_permission_course(self.user_1, self.permission_1.name, self.course_1.id)

    def test_user_has_permission_org_with_anonymous_user(self):
        """
        Test that user_has_permission_org returns False when the user is anonymous
        """
        assert not user_has_permission_org(self.anonymous_user, self.permission_1.name, self.organization_1.name)

    def test_user_has_permission_org_with_organization_level_permission(self):
        """
        Test that user_has_permission_org returns True when the user has the correct permission at the
        organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert user_has_permission_org(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_user_has_permission_org_without_organization_level_permission(self):
        """
        Test that user_has_permission_org returns False when the user does not have the correct permission at
        the organization level
        """
        assert not user_has_permission_org(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_user_has_permission_org_with_course_level_permission(self):
        """
        Test that user_has_permission_org returns False when the user has the permission but at the course
        level, and has not been granted the permission at the organization level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert not user_has_permission_org(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_user_has_permission_org_with_instance_level_permission(self):
        """
        Test that user_has_permission_org returns False when the user has the permission but at the instance
        level, and has not been granted the permission at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1)
        assert not user_has_permission_org(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_user_has_permission_org_with_permission_in_another_organization(self):
        """
        Test that user_has_permission_org returns False when the user has the permission at the
        organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_2)
        assert not user_has_permission_org(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_user_has_permission_list_course_with_anonymous_user(self):
        """
        Test that user_has_permission_list_course returns False when the user is anonymous
        """
        assert not user_has_permission_list_course(self.anonymous_user, [self.permission_1.name], self.course_1.id)

    def test_user_has_permission_list_course_with_course_level_permission(self):
        """
        Test that user_has_permission_list_course returns True when the user has the correct list of permissions
        at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert user_has_permission_list_course(self.user_1, test_permissions, self.course_1.id)

    def test_user_has_permission_list_course_without_course_level_permission(self):
        """
        Test that user_has_permission_list_course returns False when the user does not have the correct list of
        permissions at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course(self.user_1, test_permissions, self.course_1.id)

    def test_user_has_permission_list_course_with_organization_level_permission(self):
        """
        Test that user_has_permission_list_course returns False when the user has the list of permissions but at the
        organization level, and has not been granted the permissions at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course(self.user_1, test_permissions, self.course_1.id)

    def test_user_has_permission_list_course_with_instance_level_permission(self):
        """
        Test that user_has_permission_list_course returns False when the user has the list of permissions but at the
        instance level, and has not been granted the permissions at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course(self.user_1, test_permissions, self.course_1.id)

    def test_user_has_permission_list_course_with_permission_in_another_course(self):
        """
        Test that user_has_permission_list_course returns False when the user has the list of permissions at the
        course level, but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_2.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course(self.user_1, test_permissions, self.course_1.id)

    def test_user_has_permission_list_org_with_anonymous_user(self):
        """
        Test that user_has_permission_list_org returns False when the user is anonymous
        """
        assert not user_has_permission_list_org(
            self.anonymous_user, [self.permission_1.name], self.organization_1.name
        )

    def test_course_permission_list_check_any_with_a_permission_in_the_course(self):
        """
        Test that the course_permisison_list_check_any returns True when the user has any of
        the permissions on the list at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1,
            role=self.role_1,
            course_id=self.course_1.id,
            org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert user_has_permission_list_any_course(self.user_1, test_permissions, self.course_1.id)

    def test_course_permission_list_check_any_with_no_permission_in_the_course(self):
        """
        Test that the course_permisison_list_check_any returns Fale when the user has none of
        the permissions on the list at the course level
        """
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_any_course(self.user_1, test_permissions, self.course_1.id)

    def test_course_permission_list_check_any_with_a_permission_in_a_different_course(self):
        """
        Test that the course_permisison_list_check_any returns Fale when the user has a permission in the list,
        but not on the correct course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_2.name]
        assert not user_has_permission_list_any_course(self.user_1, test_permissions, self.course_1.id)

    def test_user_has_permission_list_org_with_organization_level_permission(self):
        """
        Test that user_has_permission_list_org returns True when the user has the correct list of permissions
        at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert user_has_permission_list_org(self.user_1, test_permissions, self.organization_1.name)

    def test_user_has_permission_list_org_without_organization_level_permission(self):
        """
        Test that user_has_permission_list_org returns False when the user does not have the correct list of
        permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_org(self.user_1, test_permissions, self.organization_1.name)

    def test_user_has_permission_list_org_with_course_level_permission(self):
        """
        Test that user_has_permission_list_org returns False when the user has the list of permissions but at
        the course level, and has not been granted the permissions at the organization level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_org(self.user_1, test_permissions, self.organization_1.name)

    def test_user_has_permission_list_org_with_instance_level_permission(self):
        """
        Test that user_has_permission_list_org returns False when the user has the list of permissions but at
        the instance level, and has not been granted the permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_org(self.user_1, test_permissions, self.organization_1.name)

    def test_user_has_permission_list_org_with_permission_in_another_organization(self):
        """
        Test that user_has_permission_list_org returns False when the user has the list of permissions at
        the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_org(self.user_1, test_permissions, self.organization_1.name)

    def test_user_has_permission_course_org_with_anonymous_user(self):
        """
        Test that user_has_permission_course_org returns False when the user is anonymous
        """
        assert not user_has_permission_course_org(
            self.anonymous_user, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_course_level_permission(self):
        """
        Test that user_has_permission_course_org returns True when the user has the correct permission at
        the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_without_course_level_permission(self):
        """
        Test that user_has_permission_course_org returns False when the user does not have the correct
        permission at the course level
        """
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_organization_level_permission(self):
        """
        Test that user_has_permission_course_org returns True when the user has the correct permission at
        the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_organization_level_permission_without_org_param(self):
        """
        Test that user_has_permission_course_org returns True when the user has the correct permission at
        the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id)

    def test_user_has_permission_course_org_without_organization_level_permission(self):
        """
        Test that user_has_permission_course_org returns False when the user does not have the correct
        permission at the organization level
        """
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_instance_level_permission(self):
        """
        Test that user_has_permission_course_org returns False when the user has the permission but at the
        instance level, and has not been granted the permission at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1)
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_permission_in_another_course(self):
        """
        Test that user_has_permission_course_org returns False when the user has the permission at the
        course level, but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_2.id, org=self.organization_1
        )
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_permission_in_another_organization(self):
        """
        Test that user_has_permission_course_org returns False when the user has the permission at the
        organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_2)
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_user_has_permission_course_org_with_permission_in_another_course_and_organization(self):
        """
        Test that user_has_permission_course_org returns False when the user has the permission at the
        course level, but in another course and the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_2.id, org=self.organization_2
        )
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_course_level_permission(self):
        """
        Test that user_has_permission_course_org returns True when the user has the correct list of
        permissions at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_without_course_level_permission(self):
        """
        Test that user_has_permission_course_org returns False when the user does not have the correct list
        of permissions at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_organization_level_permission(self):
        """
        Test that user_has_permission_course_org returns True when the user has the correct list of
        permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_without_organization_level_permission(self):
        """
        Test that user_has_permission_course_org returns False when the user does not have the correct list
        of permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_instance_level_permission(self):
        """
        Test that user_has_permission_course_org returns False when the user has the list of permissions but
        at the instance level, and has not been granted the permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_permission_in_another_course(self):
        """
        Test that user_has_permission_course_org returns False when the user has the list of permissions at
        the course level, but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_2.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_permission_in_another_organization(self):
        """
        Test that user_has_permission_course_org returns False when the user has the list of permissions at
        the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_permission_in_another_course_and_organization(self):
        """
        Test that user_has_permission_course_org returns False when the user has the list of permissions at
        the course level, but in another course and the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_2.id, org=self.organization_2
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_user_has_permission_course_with_waffle_flag_disabled(self):
        """
        Tests that the helper function returns false if the USE_PERMISSION_CHECKS_FLAG is not enabled
        Uses the same data as the earlier test, with the only difference being the waffle flag value
        """
        assert not user_has_permission_course(self.user_1, self.permission_1.name, self.course_1.id)

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_user_has_permission_list_course_with_waffle_flag_disabled(self):
        """
        Tests that the helper function returns false if the USE_PERMISSION_CHECKS_FLAG is not enabled
        Uses the same data as the earlier test, with the only difference being the waffle flag value
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course(self.user_1, test_permissions, self.course_1.id)

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_user_has_permission_org_with_waffle_flag_disabled(self):
        """
        Tests that the helper function returns false if the USE_PERMISSION_CHECKS_FLAG is not enabled
        Uses the same data as the earlier test, with the only difference being the waffle flag value
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert not user_has_permission_org(self.user_1, self.permission_1.name, self.organization_1.name)

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_user_has_permission_list_org_with_waffle_flag_disabled(self):
        """
        Tests that the helper function returns false if the USE_PERMISSION_CHECKS_FLAG is not enabled
        Uses the same data as the earlier test, with the only difference being the waffle flag value
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_org(self.user_1, test_permissions, self.organization_1.name)

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_user_has_permission_course_org_with_waffle_flag_disabled(self):
        """
        Tests that the helper function returns false if the USE_PERMISSION_CHECKS_FLAG is not enabled
        Uses the same data as the earlier test, with the only difference being the waffle flag value
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert not user_has_permission_course_org(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_course_or_organization_list_permission_check_with_waffle_flag_disabled(self):
        """
        Tests that the helper function returns false if the USE_PERMISSION_CHECKS_FLAG is not enabled
        Uses the same data as the earlier test, with the only difference being the waffle flag value
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not user_has_permission_list_course_org(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )


@ddt.ddt
class GetAllUserPermissionsTestcase(SharedModuleStoreTestCase):
    """
    Tests of get_all_user_permissions_for_a_course function in course_roles.helpers module
    """

    def setUp(self):
        super().setUp()
        self.user_1 = UserFactory(username="test_user_1")
        self.user_2 = UserFactory(username="test_user_2")
        self.organization_1 = OrganizationFactory(name="test_organization_1")
        self.course_1 = CourseFactory.create(
            display_name="test course 1", run="Testing_course_1", org=self.organization_1.name
        )
        self.role_1 = CourseRolesRole.objects.create(name="test_role_1")
        self.role_2 = CourseRolesRole.objects.create(name="test_role_2")
        self.role_3 = CourseRolesRole.objects.create(name="test_role_3")
        self.role_4 = CourseRolesRole.objects.create(name="test_role_4")
        self.role_5 = CourseRolesRole.objects.create(name="test_role_5")
        self.service = CourseRolesService.objects.create(name="test_service")
        self.role_1.services.add(self.service)
        self.role_2.services.add(self.service)
        self.role_3.services.add(self.service)
        self.role_4.services.add(self.service)
        self.role_5.services.add(self.service)
        self.permission_1 = CourseRolesPermission.objects.create(name="test_permission_1")
        self.permission_2 = CourseRolesPermission.objects.create(name="test_permission_2")
        self.permission_3 = CourseRolesPermission.objects.create(name="test_permission_3")
        self.permission_4 = CourseRolesPermission.objects.create(name="test_permission_4")
        self.permission_5 = CourseRolesPermission.objects.create(name="test_permission_5")
        self.role_1.permissions.add(self.permission_1)
        self.role_2.permissions.add(self.permission_2)
        self.role_3.permissions.add(self.permission_3)
        self.role_4.permissions.add(self.permission_4)
        self.role_5.permissions.add(self.permission_5)

    def test_get_all_user_permissions_for_a_course(self):
        """
        Test that get_all_user_permissions_for_a_course returns the correct permissions for the user and course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        CourseRolesUserRole.objects.create(
            user=self.user_2, role=self.role_4, course_id=self.course_1.id, org=self.organization_1
        )
        # Test that the correct permissions are returned for user_1
        assert get_all_user_permissions_for_a_course(self.user_1.id, self.course_1.id) == {self.permission_1.name}
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        # Test that the correct permissions are returned for user_1
        assert get_all_user_permissions_for_a_course(self.user_1.id, self.course_1.id) == {
            self.permission_1.name, self.permission_2.name}

        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_3, org=self.organization_1
        )
        # Test that the correct permissions are returned for user_1, including org level permissions
        assert get_all_user_permissions_for_a_course(self.user_1.id, self.course_1.id) == {
            self.permission_1.name, self.permission_2.name, self.permission_3.name}
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_5
        )
        # Test that the correct permissions are returned for user_1, including instance level permissions
        assert get_all_user_permissions_for_a_course(self.user_1.id, self.course_1.id) == {
            self.permission_1.name, self.permission_2.name, self.permission_3.name, self.permission_5.name}

    def test_get_all_user_permissions_for_a_course_with_no_permissions(self):
        """
        Test that get_all_user_permissions_for_a_course returns an empty list when the user has no permissions
        """
        assert not get_all_user_permissions_for_a_course(self.user_1.id, self.course_1.id)

    @ddt.data(
        (None, 'course_id'),
        (1, None),
        (None, None),
    )
    @ddt.unpack
    def test_get_all_user_permissions_for_a_course_with_none_values(self, user_id, course_id):
        """
        Test that get_all_user_permissions_for_a_course raises value error when the user has no permissions
        """
        with pytest.raises(ValueError):
            get_all_user_permissions_for_a_course(user_id, course_id)

    def test_get_all_user_permissions_for_a_course_with_invalid_user(self):
        """
        Test that get_all_user_permissions_for_a_course raises value error when the user not exist
        """
        with pytest.raises(ValueError):
            get_all_user_permissions_for_a_course(999, 999)

    def test_get_all_user_permissions_for_a_course_with_invalid_course(self):
        """
        Test that get_all_user_permissions_for_a_course raises value error when the course not exist
        """
        with pytest.raises(ValueError):
            get_all_user_permissions_for_a_course(self.user_1.id, 999)
