"""
Tests of the course_roles.helpers module
"""
from organizations.tests.factories import OrganizationFactory

from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory
from openedx.core.djangoapps.course_roles.helpers import (
    course_or_organization_permission_check,
    course_or_organization_permission_list_check,
    course_permission_check,
    course_permissions_list_check,
    organization_permission_check,
    organization_permissions_list_check
)
from openedx.core.djangoapps.course_roles.models import (
    CourseRolesPermission,
    CourseRolesRole,
    CourseRolesService,
    CourseRolesUserRole
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class PermissionCheckTestCase(SharedModuleStoreTestCase):
    """
    Tests of the permission check functions in course_roles.helpers module
    """

    def setUp(self):
        super().setUp()
        self.anonymous_user = AnonymousUserFactory()
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

    def test_course_permission_check_with_anonymus_user(self):
        """
        Test that course_permission_check returns False when the user is anonymous
        """
        assert not course_permission_check(self.anonymous_user, self.permission_1.name, self.course_1.id)

    def test_course_permission_check_with_course_level_permission(self):
        """
        Test that course_permission_check returns True when the user has the correct permission at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert course_permission_check(self.user_1, self.permission_1.name, self.course_1.id)

    def test_course_permission_check_without_course_level_permission(self):
        """
        Test that course_permission_check returns False when the user does not have the correct permission at the
        course level
        """
        assert not course_permission_check(self.user_1, self.permission_1.name, self.course_1.id)

    def test_course_permision_check_with_organization_level_permission(self):
        """
        Test that course_permission_check returns False when the user has the permission but at the organization
        level, and has not been granted the permission at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert not course_permission_check(self.user_1, self.permission_1.name, self.course_1.id)

    def test_course_permission_check_with_instance_level_permission(self):
        """
        Test that course_permission_check returns False when the user has the permission but at the instance level,
        and has not been granted the permission at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1)
        assert not course_permission_check(self.user_1, self.permission_1.name, self.course_1.id)

    def test_course_permission_check_with_permission_in_another_course(self):
        """
        Test that course_permission_check returns False when the user has the permission at the course level,
        but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_2.id, org=self.organization_1
        )
        assert not course_permission_check(self.user_1, self.permission_1.name, self.course_1.id)

    def test_organization_permission_check_with_anonymous_user(self):
        """
        Test that organization_permission_check returns False when the user is anonymous
        """
        assert not organization_permission_check(self.anonymous_user, self.permission_1.name, self.organization_1.name)

    def test_organization_permission_check_with_organization_level_permission(self):
        """
        Test that organization_permission_check returns True when the user has the correct permission at the
        organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert organization_permission_check(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_organization_permission_check_without_organization_level_permission(self):
        """
        Test that organization_permission_check returns False when the user does not have the correct permission at
        the organization level
        """
        assert not organization_permission_check(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_organization_permission_check_with_course_level_permission(self):
        """
        Test that organization_permission_check returns False when the user has the permission but at the course
        level, and has not been granted the permission at the organization level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert not organization_permission_check(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_organization_permission_check_with_instance_level_permission(self):
        """
        Test that organization_permission_check returns False when the user has the permission but at the instance
        level, and has not been granted the permission at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1)
        assert not organization_permission_check(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_organization_permission_check_with_permission_in_another_organization(self):
        """
        Test that organization_permission_check returns False when the user has the permission at the
        organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_2)
        assert not organization_permission_check(self.user_1, self.permission_1.name, self.organization_1.name)

    def test_course_permissions_list_check_with_anonymous_user(self):
        """
        Test that course_permissions_list_check returns False when the user is anonymous
        """
        assert not course_permissions_list_check(self.anonymous_user, [self.permission_1.name], self.course_1.id)

    def test_course_permissions_list_check_with_course_level_permission(self):
        """
        Test that course_permissions_list_check returns True when the user has the correct list of permissions
        at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert course_permissions_list_check(self.user_1, test_permissions, self.course_1.id)

    def test_course_permissions_list_check_without_course_level_permission(self):
        """
        Test that course_permissions_list_check returns False when the user does not have the correct list of
        permissions at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_permissions_list_check(self.user_1, test_permissions, self.course_1.id)

    def test_course_permissions_list_check_with_organization_level_permission(self):
        """
        Test that course_permissions_list_check returns False when the user has the list of permissions but at the
        organization level, and has not been granted the permissions at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_permissions_list_check(self.user_1, test_permissions, self.course_1.id)

    def test_course_permissions_list_check_with_instance_level_permission(self):
        """
        Test that course_permissions_list_check returns False when the user has the list of permissions but at the
        instance level, and has not been granted the permissions at the course level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_permissions_list_check(self.user_1, test_permissions, self.course_1.id)

    def test_course_permissions_list_check_with_permission_in_another_course(self):
        """
        Test that course_permissions_list_check returns False when the user has the list of permissions at the
        course level, but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_2.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_permissions_list_check(self.user_1, test_permissions, self.course_1.id)

    def test_organization_permissions_list_check_with_anonymous_user(self):
        """
        Test that organization_permissions_list_check returns False when the user is anonymous
        """
        assert not organization_permissions_list_check(
            self.anonymous_user, [self.permission_1.name], self.organization_1.name
        )

    def test_organization_permissions_list_check_with_organization_level_permission(self):
        """
        Test that organization_permissions_list_check returns True when the user has the correct list of permissions
        at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert organization_permissions_list_check(self.user_1, test_permissions, self.organization_1.name)

    def test_organization_permissions_list_check_without_organization_level_permission(self):
        """
        Test that organization_permissions_list_check returns False when the user does not have the correct list of
        permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not organization_permissions_list_check(self.user_1, test_permissions, self.organization_1.name)

    def test_organization_permissions_list_check_with_course_level_permission(self):
        """
        Test that organization_permissions_list_check returns False when the user has the list of permissions but at
        the course level, and has not been granted the permissions at the organization level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not organization_permissions_list_check(self.user_1, test_permissions, self.organization_1.name)

    def test_organization_permissions_list_check_with_instance_level_permission(self):
        """
        Test that organization_permissions_list_check returns False when the user has the list of permissions but at
        the instance level, and has not been granted the permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not organization_permissions_list_check(self.user_1, test_permissions, self.organization_1.name)

    def test_organization_permissions_list_check_with_permission_in_another_organization(self):
        """
        Test that organization_permissions_list_check returns False when the user has the list of permissions at
        the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not organization_permissions_list_check(self.user_1, test_permissions, self.organization_1.name)

    def test_course_or_organization_permission_check_with_anonymous_user(self):
        """
        Test that course_or_organization_permission_check returns False when the user is anonymous
        """
        assert not course_or_organization_permission_check(
            self.anonymous_user, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_course_level_permission(self):
        """
        Test that course_or_organization_permission_check returns True when the user has the correct permission at
        the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_without_course_level_permission(self):
        """
        Test that course_or_organization_permission_check returns False when the user does not have the correct
        permission at the course level
        """
        assert not course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_organization_level_permission(self):
        """
        Test that course_or_organization_permission_check returns True when the user has the correct permission at
        the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_organization_level_permission_without_org_param(self):
        """
        Test that course_or_organization_permission_check returns True when the user has the correct permission at
        the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        assert course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id)

    def test_course_or_organization_permission_check_without_organization_level_permission(self):
        """
        Test that course_or_organization_permission_check returns False when the user does not have the correct
        permission at the organization level
        """
        assert not course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_instance_level_permission(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the permission but at the
        instance level, and has not been granted the permission at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1)
        assert not course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_permission_in_another_course(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the permission at the
        course level, but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_2.id, org=self.organization_1
        )
        assert not course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_permission_in_another_organization(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the permission at the
        organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_2)
        assert not course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_permission_check_with_permission_in_another_course_and_organization(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the permission at the
        course level, but in another course and the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_2.id, org=self.organization_2
        )
        assert not course_or_organization_permission_check(
            self.user_1, self.permission_1.name, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_course_level_permission(self):
        """
        Test that course_or_organization_permission_check returns True when the user has the correct list of
        permissions at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_without_course_level_permission(self):
        """
        Test that course_or_organization_permission_check returns False when the user does not have the correct list
        of permissions at the course level
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_organization_level_permission(self):
        """
        Test that course_or_organization_permission_check returns True when the user has the correct list of
        permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_without_organization_level_permission(self):
        """
        Test that course_or_organization_permission_check returns False when the user does not have the correct list
        of permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_1, org=self.organization_1)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_instance_level_permission(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the list of permissions but
        at the instance level, and has not been granted the permissions at the organization level
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_permission_in_another_course(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the list of permissions at
        the course level, but in another course
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_2.id, org=self.organization_1
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_permission_in_another_organization(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the list of permissions at
        the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(user=self.user_1, role=self.role_2, org=self.organization_2)
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )

    def test_course_or_organization_list_permission_check_with_permission_in_another_course_and_organization(self):
        """
        Test that course_or_organization_permission_check returns False when the user has the list of permissions at
        the course level, but in another course and the organization level, but in another organization
        """
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_2.id, org=self.organization_2
        )
        test_permissions = [self.permission_1.name, self.permission_2.name]
        assert not course_or_organization_permission_list_check(
            self.user_1, test_permissions, self.course_1.id, self.organization_1.name
        )
