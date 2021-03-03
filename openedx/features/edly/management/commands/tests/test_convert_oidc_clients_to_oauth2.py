"""
Tests the "convert_oidc_clients_to_oauth2" management command.
"""

from django.core.management import call_command
from django.test import TestCase
from oauth2_provider.models import get_application_model

from openedx.core.djangoapps.oauth_dispatch.models import ApplicationAccess
from .factories import ClientFactory
from ..convert_oidc_clients_to_oauth2 import Command

Application = get_application_model()


class TestConvertOIDCClientsToOauth2(TestCase):
    """
    Tests the "convert_oidc_clients_to_oauth2" management command.
    """
    def setUp(self):
        super(TestConvertOIDCClientsToOauth2, self).setUp()
        self.oidc_client = ClientFactory.create()

    def test_convert_oidc_to_oauth2_application(self):
        """
        Verify oidc to oauth2 clients conversion happens successfully.
        """
        call_command(Command())

        application = Application.objects.filter(name=self.oidc_client.name).first()
        assert application.name == self.oidc_client.name
        assert application.client_id == self.oidc_client.client_id
        assert application.client_secret == self.oidc_client.client_secret

        application_access = ApplicationAccess.objects.filter(application_id=application.id).first()
        assert application_access
