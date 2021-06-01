"""
Tests to ensure the Tahoe Registration API end-point allows multi-tenant emails.
"""

from mock import patch
from unittest import skipUnless, skipIf

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms

from .test_utils import with_organization_context

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@skip_unless_lms
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.permission_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.throttle_classes', [])
@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This only tests multi-tenancy')
class MultiTenantRegistrationAPITest(APITestCase):
    """
    Tests to ensure the Tahoe Registration API end-point allow multi-tenant emails.
    """

    EMAIL = 'learner@example.com'
    PASSWORD = 'test'

    def setUp(self):
        super(MultiTenantRegistrationAPITest, self).setUp()
        self.url = reverse('tahoe-api:v1:registrations-list')

    def register_user(self, username):
        return self.client.post(self.url, {
            'username': username,
            'password': self.PASSWORD,
            'email': self.EMAIL,
            'name': 'Learner'
        })

    def test_register_duplicate_email_same_org(self):
        """
        The APPSEMBLER_MULTI_TENANT_EMAILS feature should prevent email reuse within the same organization.
        """
        with with_organization_context(site_color='red1'):
            response_1 = self.register_user('learner1')
            assert response_1.status_code == status.HTTP_200_OK, response_1.content

            response_2 = self.register_user('learner2')  # Same email
            assert response_2.status_code == status.HTTP_409_CONFLICT, response_2.content

    def test_register_reuse_email_two_orgs(self):
        """
        The APPSEMBLER_MULTI_TENANT_EMAILS feature should allow email reuse in two different orgs.
        """
        color1 = 'red1'
        with with_organization_context(site_color=color1):
            red_response = self.register_user('red_learner')
            assert red_response.status_code == status.HTTP_200_OK, '{} {}'.format(color1, red_response.content)

        color2 = 'blue2'
        with with_organization_context(site_color=color2):
            blue_response = self.register_user('blue_learner')  # Same email
            assert blue_response.status_code == status.HTTP_200_OK, '{} {}'.format(color2, blue_response.content)
