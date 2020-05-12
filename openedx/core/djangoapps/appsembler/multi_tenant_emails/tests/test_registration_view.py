import json
from unittest import skipUnless

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms

from .test_utils import with_organization_context


@skip_unless_lms
@override_settings(DEFAULT_SITE_THEME='edx-theme-codebase')
@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This only tests multi-tenancy')
class MultiTenantRegistrationViewTest(APITestCase):
    """
    Tests to ensure the registration end-point allow multi-tenant emails.
    """

    EMAIL = 'ali@example.com'
    PASSWORD = 'zzz'

    def setUp(self):
        super(MultiTenantRegistrationViewTest, self).setUp()
        self.url = reverse('user_api_registration')

    def register_user(self, color):
        # Register the first user
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'name': 'Ali',
            'username': 'ali_{}'.format(color),
            'password': self.PASSWORD,
            'honor_code': 'true',
        })
        assert response.status_code == status.HTTP_200_OK, '{}: {}'.format(color, response.content)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            'email': self.EMAIL,
            'name': 'Ali Trying Again',
            'username': 'ali_again_{}'.format(color),
            'password': self.PASSWORD,
            'honor_code': 'true',
        })
        assert response.status_code == status.HTTP_409_CONFLICT, '{}: {}'.format(color, response.content)
        response_json = json.loads(response.content)
        assert response_json == {
            'email': [{
                'user_message': (
                    'It looks like {} belongs to an existing account. '
                    'Try again with a different email address.'
                ).format(
                    self.EMAIL
                )
            }]
        }, color

    def test_register_duplicate_email(self):
        color1 = 'red1'
        with with_organization_context(site_color=color1):
            self.register_user(color1)

        color2 = 'blue2'
        with with_organization_context(site_color=color2):
            self.register_user(color2)
