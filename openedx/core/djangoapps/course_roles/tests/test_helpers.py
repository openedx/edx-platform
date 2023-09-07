"""
Tests of the course_roles.helpers module
"""
from organizations.tests.factories import OrganizationFactory

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.course_roles.helpers import permission_check
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
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")
        self.user = UserFactory(username='test_user_1')
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
        CourseRolesRolePermissions.objects.create(role=self.role, permission=self.permission_1, allowed=True)
        CourseRolesUserRole.objects.create(
            user=self.user,
            role=self.role,
            course_id=self.course.id,
            org=self.organization
            )
