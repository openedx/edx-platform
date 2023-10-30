import ddt
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APIClient
from organizations.tests.factories import OrganizationFactory

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.course_roles.models import (
    CourseRolesPermission,
    CourseRolesRole,
    CourseRolesService,
    CourseRolesUserRole,
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class UserPermissionsViewTestCase(SharedModuleStoreTestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_1 = UserFactory(username="test_user_1")
        self.organization_1 = OrganizationFactory(name="test_organization_1")
        self.course_1 = CourseFactory.create(
            display_name="test course 1", run="Testing_course_1", org=self.organization_1.name
        )
        self.role_1 = CourseRolesRole.objects.create(name="test_role_1")
        self.service = CourseRolesService.objects.create(name="test_service")
        self.role_1.services.add(self.service)
        self.permission_1 = CourseRolesPermission.objects.create(name="test_permission_1")
        self.permission_2 = CourseRolesPermission.objects.create(name="test_permission_2")
        self.role_1.permissions.add(self.permission_1)
        self.role_1.permissions.add(self.permission_2)
        CourseRolesUserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )

    def test_get_user_permissions_without_login(self):
        # Test get user permissions without login.
        querykwargs = {'course_id': self.course_1.id, 'user_id': self.user_1.id}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_permissions_view(self):
        querykwargs = {'course_id': self.course_1.id, 'user_id': self.user_1.id}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        expected_api_response = {'permissions': {self.permission_1.name, self.permission_2.name}}
        # Ensure the view returns a 200 OK status code
        self.client.login(username=self.user_1, password='test')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure the view returns the correct permissions for the user
        self.assertEqual(response.data['permissions'], expected_api_response['permissions'])

    @ddt.data(
        (None, None),
        (None, "course_id"),
        (1, None)
    )
    @ddt.unpack
    def test_get_user_permission_view_without_queryargs(self, user_id, course_id):
        # Test get user permissions without queryargs.
        querykwargs = {'course_id': course_id, 'user_id': user_id}
        querykwargs = {k: v for k, v in querykwargs.items() if v is not None}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        self.client.login(username=self.user_1, password='test')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_permission_view_with_invalid_queryargs(self):
        # Test get user permissions with invalid queryargs.
        self.client.login(username=self.user_1, password='test')
        org = 'org1'
        number = 'course1'
        run = 'run1'
        course_id = self.store.make_course_key(org, number, run)
        querykwargs = {'course_id': course_id, 'user_id': self.user_1.id}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        querykwargs = {'course_id': self.course_1.id, 'user_id': 999}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
