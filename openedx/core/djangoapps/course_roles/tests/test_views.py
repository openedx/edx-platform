"""
Tests for the course_roles views.
"""
import ddt
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APIClient
from organizations.tests.factories import OrganizationFactory

from common.djangoapps.student.tests.factories import UserFactory
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_roles.toggles import USE_PERMISSION_CHECKS_FLAG
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.models import (
    Permission,
    Role,
    Service,
    UserRole
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class UserPermissionsViewTestCase(SharedModuleStoreTestCase):
    """
    Tests for the UserPermissionsView.
    """
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user_1 = UserFactory(username="test_user_1", password="test")
        self.organization_1 = OrganizationFactory(name="test_organization_1")
        self.course_1 = CourseFactory.create(
            display_name="test course 1", run="Testing_course_1", org=self.organization_1.name
        )
        CourseOverview.load_from_module_store(self.course_1.id)
        self.role_1 = Role.objects.create(name="test_role_1")
        self.service = Service.objects.create(name="test_service")
        self.role_1.services.add(self.service)
        self.permission_1 = Permission.objects.create(name=CourseRolesPermission.MANAGE_CONTENT.value.name)
        self.permission_2 = Permission.objects.create(name=CourseRolesPermission.MANAGE_COURSE_SETTINGS.value.name)
        self.role_1.permissions.add(self.permission_1)
        self.role_1.permissions.add(self.permission_2)
        UserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )

    def test_get_user_permissions_without_login(self):
        """
        Test get user permissions without login.
        """
        querykwargs = {'course_id': self.course_1.id, 'user_id': self.user_1.id}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_permissions_view(self):
        """
        Test get user permissions view with valid queryargs.
        """
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
        """
        Test get user permissions without queryargs.
        """
        querykwargs = {'course_id': course_id, 'user_id': user_id}
        querykwargs = {k: v for k, v in querykwargs.items() if v is not None}
        url = f'{reverse("course_roles_api:user_permissions")}?{urlencode(querykwargs)}'
        self.client.login(username=self.user_1, password='test')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_user_permission_view_with_invalid_queryargs(self):
        """
        Test get user permissions with invalid queryargs.
        """
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


class UserPermissionsFlagViewTestCase(SharedModuleStoreTestCase):
    """
    Tests for the UserPermissionsFlagView.
    """
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.user_1 = UserFactory(username="test_user_1", password="test")

    def test_get_permission_check_flag_without_login(self):
        # user not logged in
        url = f'{reverse("course_roles_api:permission_check_flag")}'
        # request waffle flag value
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_permission_check_flag_view_no_waffle_created(self):
        url = f'{reverse("course_roles_api:permission_check_flag")}'
        expected_api_response = {'enabled': False}
        # login user
        self.client.login(username=self.user_1, password='test')
        # request waffle flag value
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], expected_api_response['enabled'])

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=False)
    def test_get_permission_check_flag_view_waffle_is_false(self):
        url = f'{reverse("course_roles_api:permission_check_flag")}'
        expected_api_response = {'enabled': False}
        # login user
        self.client.login(username=self.user_1, password='test')
        # request waffle flag value
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], expected_api_response['enabled'])

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=True)
    def test_get_permission_check_flag_view_waffle_is_true(self):
        url = f'{reverse("course_roles_api:permission_check_flag")}'
        expected_api_response = {'enabled': True}
        # login user
        self.client.login(username=self.user_1, password='test')
        # request waffle flag value
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['enabled'], expected_api_response['enabled'])
