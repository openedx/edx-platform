"""
Test the use cases of the views of the mfe api.
"""

from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from rest_framework import status

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.api.test_utils import ApiTestCase


class MFEConfigTestCase(ApiTestCase):
    """
    Test the use case that exposes the site configuration with the mfe api.
    """
    def setUp(self):
        self.mfe_config_api_url = reverse('mfe_api:config')
        return super().setUp()

    def test_get_mfe_config(self):
        """Test the get mfe config from site configuration with the mfe api.

        Expected result:
        - Inside self.get_json pass the response is a json and the status is 200 asserts.
        - The configuration obtained by the api is equal to its site configuration in the
        MFE_CONFIG key.
        """
        mfe_config = configuration_helpers.get_value('MFE_CONFIG', {})
        response_json = self.get_json(self.mfe_config_api_url)
        assert response_json == mfe_config

    @patch.dict(settings.FEATURES, {'ENABLE_MFE_API': False})
    def test_404_get_mfe_config(self):
        """Test the 404 not found response from get mfe config.

        Expected result:
        - Response status code equal to 404
        """
        response = self.client.get(self.mfe_config_api_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
