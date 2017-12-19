"""
Tests for User deactivation API permissions
"""
from django.test import TestCase, RequestFactory

from openedx.core.djangoapps.user_api.accounts.permissions import CanDeactivateUser
from student.tests.factories import ContentTypeFactory, PermissionFactory, SuperuserFactory, UserFactory


class CanDeactivateUserTest(TestCase):
    """ Tests for user deactivation API permissions """

    def setUp(self):
        super(CanDeactivateUserTest, self).setUp()
        self.request = RequestFactory().get('/test/url')

    def test_api_permission_superuser(self):
        self.request.user = SuperuserFactory()

        result = CanDeactivateUser().has_permission(self.request, None)
        self.assertTrue(result)

    def test_api_permission_user_granted_permission(self):
        user = UserFactory()
        permission = PermissionFactory(
            codename='can_deactivate_users',
            content_type=ContentTypeFactory(
                app_label='student'
            )
        )
        user.user_permissions.add(permission)  # pylint: disable=no-member
        self.request.user = user

        result = CanDeactivateUser().has_permission(self.request, None)
        self.assertTrue(result)

    def test_api_permission_user_without_permission(self):
        self.request.user = UserFactory()
        result = CanDeactivateUser().has_permission(self.request, None)
        self.assertFalse(result)
