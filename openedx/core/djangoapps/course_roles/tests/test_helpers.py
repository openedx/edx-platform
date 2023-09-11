"""
Tests of the course_roles.helpers module
"""
from organizations.tests.factories import OrganizationFactory

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.course_roles.helpers import course_permission_check, organization_permission_check
from openedx.core.djangoapps.course_roles.models import (
    CourseRolesPermission,
    CourseRolesRole,
    CourseRolesRolePermissions,
    CourseRolesService,
    CourseRolesUserRole
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class PermissionCheckTestCase(SharedModuleStoreTestCase):
    def setUp(self):
        super().setUp()
        self.organization = OrganizationFactory(name='test_organization')
        self.organization_2 = OrganizationFactory(name='test_organization_2')
        self.course = CourseFactory.create(display_name='test course', run="Testing_course", org=self.organization.name)
        self.user = UserFactory(username='test_user_1')
        self.user_2 = UserFactory(username='test_user_2')
        self.user_3 = UserFactory(username='test_user_3')
        self.service = CourseRolesService.objects.create(name='test_service')
        self.permission_1 = CourseRolesPermission.objects.create(
            name='test_permission_1',
            description='test_description_1'
            )
        self.permission_2 = CourseRolesPermission.objects.create(
            name='test_permission_2',
            description='test_description_2'
            )
        self.role = CourseRolesRole.objects.create(
            name='test_role',
            short_description='test_short_description',
            long_description='test_long_description',
            service=self.service
            )
        CourseRolesRolePermissions.objects.create(role=self.role, permission=self.permission_1)
        CourseRolesUserRole.objects.create(
            user=self.user,
            role=self.role,
            course_id=self.course.id,
            org=self.organization
            )
        CourseRolesUserRole.objects.create(
            user=self.user_2,
            role=self.role,
            org=self.organization
            )
        CourseRolesUserRole.objects.create(
            user=self.user_3,
            role=self.role,
            org=self.organization_2
            )

    def test_permission_check_with_correct_course_permission(self):
        assert course_permission_check(self.user, self.permission_1.name, self.course.id)

    def test_permission_check_without_course_permission(self):
        assert not course_permission_check(self.user, self.permission_2.name, self.course.id)

    def test_permission_check_with_correct_organization_permission(self):
        assert organization_permission_check(self.user_2, self.permission_1.name, self.organization.name)

    def test_permission_check_without_organization_permission(self):
        assert not organization_permission_check(self.user_3, self.permission_1.name, self.organization.name)
