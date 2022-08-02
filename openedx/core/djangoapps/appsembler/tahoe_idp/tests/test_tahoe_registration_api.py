"""
Tests to ensure the Tahoe Registration API is disabled if `tahoe-idp` is in use.
"""
import ddt
from mock import patch

from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APITestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms

from ...multi_tenant_emails.tests.test_utils import with_organization_context

APPSEMBLER_API_VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.api.v1.views'


@skip_unless_lms
@ddt.ddt
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.authentication_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.permission_classes', [])
@patch(APPSEMBLER_API_VIEWS_MODULE + '.RegistrationViewSet.throttle_classes', [])
class TahoeIdPDisablesRegisrationAPITest(APITestCase):
    """
    Tests to ensure the Tahoe Registration API end-point allow multi-tenant emails.
    """

    EMAIL = 'learner@example.com'
    PASSWORD = 'test'

    def register_user(self, url, username):
        return self.client.post(url, {
            'username': username,
            'password': self.PASSWORD,
            'email': self.EMAIL,
            'name': 'Learner',
        })

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_IDP': False})
    @ddt.data(
        reverse_lazy('tahoe-api:v1:registrations-list'),
        reverse_lazy('tahoe-api:v2:registrations-list'),
    )
    def test_api_without_tahoe_idp(self, url):
        """
        Both v1 and v2 API should work with Tahoe IdP.
        """
        color1 = 'red1'
        with with_organization_context(site_color=color1):
            response = self.register_user(url, 'red_learner')
            content = response.content.decode('utf-8')
            assert response.status_code == status.HTTP_200_OK, '{} {}'.format(color1, content)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_IDP': True})
    @ddt.data(
        reverse_lazy('tahoe-api:v1:registrations-list'),
        reverse_lazy('tahoe-api:v2:registrations-list'),
    )
    def test_api_wit_tahoe_idp(self, url):
        """
        Both v1 and v2 API shouldn't work with Tahoe IdP.
        """
        color1 = 'red1'
        with with_organization_context(site_color=color1):
            response = self.register_user(url, 'red_learner')
            content = response.content.decode('utf-8')
            assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE, '{} {}'.format(color1, content)
            assert 'This API is not available for this site. Please use the Identity Provider API.' in content
