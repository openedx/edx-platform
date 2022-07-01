"""
Test the use cases of the views of the mfe api.
"""

from unittest.mock import call, patch

import ddt
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


@ddt.ddt
class MFEConfigTestCase(APITestCase):
    """
    Test the use case that exposes the site configuration with the mfe api.
    """
    def setUp(self):
        self.mfe_config_api_url = reverse("mfe_api:config")
        return super().setUp()

    @patch("lms.djangoapps.mfe_api.views.configuration_helpers")
    def test_get_mfe_config(self, configuration_helpers_mock):
        """Test the get mfe config from site configuration with the mfe api.

        Expected result:
        - Inside self.get_json pass the response is a json and the status is 200 asserts.
        - The configuration obtained by the api is equal to its site configuration in the
        MFE_CONFIG key.
        """
        configuration_helpers_mock.get_value.return_value = {"logo": "logo.jpg"}
        response = self.client.get(self.mfe_config_api_url)

        configuration_helpers_mock.get_value.assert_called_once_with("MFE_CONFIG", {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"logo": "logo.jpg"})

    @patch("lms.djangoapps.mfe_api.views.configuration_helpers")
    def test_get_mfe_config_with_queryparams(self, configuration_helpers_mock):
        """Test the get mfe config with a query params from site configuration.

        Expected result:
        - Inside self.get_json pass the response is a json and the status is 200 asserts.
        - The configuration obtained by the api is equal to its site configuration in the
        MFE_CONFIG and MFE_CONFIG_MYMFE merged on top.
        """
        configuration_helpers_mock.get_value.side_effect = [{"logo": "logo.jpg", "other": "other"},
                                                            {"logo": "logo_mymfe.jpg"}]

        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calls = [call("MFE_CONFIG", {}), call("MFE_CONFIG_MYMFE", {})]
        configuration_helpers_mock.get_value.assert_has_calls(calls)
        self.assertEqual(response.json(), {"logo": "logo_mymfe.jpg", "other": "other"})

    @patch("lms.djangoapps.mfe_api.views.configuration_helpers")
    @ddt.data(
        [{}, {}, {}],
        [{"logo": "logo.jpg"}, {}, {"logo": "logo.jpg"}],
        [{}, {"logo": "logo_mymfe.jpg"}, {"logo": "logo_mymfe.jpg"}],
        [{"logo": "logo.jpg"}, {"logo": "logo_mymfe.jpg"}, {"logo": "logo_mymfe.jpg"}],
        [{"logo": "logo.jpg", "other": "other"}, {"logo": "logo_mymfe.jpg"},
            {"logo": "logo_mymfe.jpg", "other": "other"}],
    )
    @ddt.unpack
    def test_get_mfe_config_with_queryparams_other_cases(
        self,
        mfe_config,
        mfe_config_mymfe,
        expected_response,
        configuration_helpers_mock
    ):
        """_summary_

        Args:
            configuration_helpers_mock (_type_): _description_
        """

        configuration_helpers_mock.get_value.side_effect = [mfe_config, mfe_config_mymfe]

        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calls = [call("MFE_CONFIG", {}), call("MFE_CONFIG_MYMFE", {})]
        configuration_helpers_mock.get_value.assert_has_calls(calls)
        self.assertEqual(response.json(), expected_response)

    @patch("lms.djangoapps.mfe_api.views.configuration_helpers")
    @override_settings(ENABLE_MFE_API=False)
    def test_404_get_mfe_config(self, configuration_helpers_mock):
        """Test the 404 not found response from get mfe config.

        Expected result:
        - Response status code equal to 404
        """
        response = self.client.get(self.mfe_config_api_url)
        configuration_helpers_mock.get_value.assert_not_called()
        assert response.status_code == status.HTTP_404_NOT_FOUND
