"""
Test the use cases of the views of the mfe api.
"""

from unittest.mock import call, patch

import ddt
from django.conf import settings
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
        self.mfe_config_api_url = reverse("mfe_config_api:config")
        return super().setUp()

    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    def test_get_mfe_config(self, configuration_helpers_mock):
        """Test the get mfe config from site configuration with the mfe api.

        Expected result:
        - The get_value method of the configuration_helpers in the views is called once with the
        parameters ("MFE_CONFIG", settings.MFE_CONFIG)
        - The status of the response of the request is a HTTP_200_OK.
        - The json of the response of the request is equal to the mocked configuration.
        """
        configuration_helpers_mock.get_value.return_value = {"EXAMPLE_VAR": "value"}
        response = self.client.get(self.mfe_config_api_url)

        configuration_helpers_mock.get_value.assert_called_once_with("MFE_CONFIG", settings.MFE_CONFIG)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"EXAMPLE_VAR": "value"})

    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    def test_get_mfe_config_with_queryparam(self, configuration_helpers_mock):
        """Test the get mfe config with a query param from site configuration.

        Expected result:
        - The get_value method of the configuration_helpers in the views is called twice, once with the
        parameters ("MFE_CONFIG", settings.MFE_CONFIG)
        and once with the parameters ("MFE_CONFIG_OVERRIDES", settings.MFE_CONFIG_OVERRIDES).
        - The json of the response is the merge of both mocked configurations.
        """
        configuration_helpers_mock.get_value.side_effect = [
            {"EXAMPLE_VAR": "value", "OTHER": "other"},
            {"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
        ]

        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calls = [call("MFE_CONFIG", settings.MFE_CONFIG),
                 call("MFE_CONFIG_OVERRIDES", settings.MFE_CONFIG_OVERRIDES)]
        configuration_helpers_mock.get_value.assert_has_calls(calls)
        self.assertEqual(response.json(), {"EXAMPLE_VAR": "mymfe_value", "OTHER": "other"})

    @ddt.unpack
    @ddt.data(
        dict(
            mfe_config={},
            mfe_config_overrides={},
            expected_response={},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={},
            expected_response={"EXAMPLE_VAR": "value"},
        ),
        dict(
            mfe_config={},
            mfe_config_overrides={"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
            expected_response={"EXAMPLE_VAR": "mymfe_value"},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
            expected_response={"EXAMPLE_VAR": "mymfe_value"},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value", "OTHER": "other"},
            mfe_config_overrides={"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
            expected_response={"EXAMPLE_VAR": "mymfe_value", "OTHER": "other"},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={"yourmfe": {"EXAMPLE_VAR": "yourmfe_value"}},
            expected_response={"EXAMPLE_VAR": "value"},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={
                "yourmfe": {"EXAMPLE_VAR": "yourmfe_value"},
                "mymfe": {"EXAMPLE_VAR": "mymfe_value"},
            },
            expected_response={"EXAMPLE_VAR": "mymfe_value"},
        ),
    )
    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    def test_get_mfe_config_with_queryparam_multiple_configs(
        self,
        configuration_helpers_mock,
        mfe_config,
        mfe_config_overrides,
        expected_response,
    ):
        """Test the get mfe config with a query param and different settings in mfe_config and mfe_config_overrides with
        the site configuration to test that the merge of the configurations is done correctly and mymfe config take
        precedence.

        Expected result:
        - The get_value method of the configuration_helpers in the views is called twice, once with the
        parameters ("MFE_CONFIG", settings.MFE_CONFIG)
        and once with the parameters ("MFE_CONFIG_OVERRIDES", settings.MFE_CONFIG_OVERRIDES).
        - The json of the response is the expected_response passed by ddt.data.
        """
        configuration_helpers_mock.get_value.side_effect = [mfe_config, mfe_config_overrides]

        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calls = [call("MFE_CONFIG", settings.MFE_CONFIG),
                 call("MFE_CONFIG_OVERRIDES", settings.MFE_CONFIG_OVERRIDES)]
        configuration_helpers_mock.get_value.assert_has_calls(calls)
        self.assertEqual(response.json(), expected_response)

    def test_get_mfe_config_from_django_settings(self):
        """Test that when there is no site configuration, the API takes the django settings.

        Expected result:
        - The status of the response of the request is a HTTP_200_OK.
        - The json response is equal to MFE_CONFIG in lms/envs/test.py"""
        response = self.client.get(self.mfe_config_api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), settings.MFE_CONFIG)

    def test_get_mfe_config_with_queryparam_from_django_settings(self):
        """Test that when there is no site configuration, the API with queryparam takes the django settings.

        Expected result:
        - The status of the response of the request is a HTTP_200_OK.
        - The json response is equal to MFE_CONFIG merged with MFE_CONFIG_OVERRIDES['mymfe']
        """
        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {**settings.MFE_CONFIG, **settings.MFE_CONFIG_OVERRIDES["mymfe"]}
        self.assertEqual(response.json(), expected)

    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    @override_settings(ENABLE_MFE_CONFIG_API=False)
    def test_404_get_mfe_config(self, configuration_helpers_mock):
        """Test the 404 not found response from get mfe config.

        Expected result:
        - The get_value method of configuration_helpers is not called.
        - The status of the response of the request is a HTTP_404_NOT_FOUND.
        """
        response = self.client.get(self.mfe_config_api_url)
        configuration_helpers_mock.get_value.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
