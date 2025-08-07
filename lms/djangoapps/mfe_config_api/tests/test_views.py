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

# Base configuration values, used in tests to build a correct expected response
default_base_config = {
    'course_about_twitter_account': '@YourPlatformTwitterAccount',
    'courses_are_browsable': True,
    'enable_course_sorting_by_start_date': True,
    'homepage_course_max': None,
    'homepage_promo_video_youtube_id': 'your-youtube-id',
    'is_cosmetic_price_enabled': False,
    'show_homepage_promo_video': False
}


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
        def side_effect(key, default=None):
            if key == "MFE_CONFIG":
                return {"EXAMPLE_VAR": "value"}
            return default
        configuration_helpers_mock.get_value.side_effect = side_effect

        response = self.client.get(self.mfe_config_api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"EXAMPLE_VAR": "value", **default_base_config})

    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    def test_get_mfe_config_with_queryparam(self, configuration_helpers_mock):
        """Test the get mfe config with a query param from site configuration.

        Expected result:
        - The get_value method of the configuration_helpers in the views is called twice, once with the
        parameters ("MFE_CONFIG", settings.MFE_CONFIG)
        and once with the parameters ("MFE_CONFIG_OVERRIDES", settings.MFE_CONFIG_OVERRIDES).
        - The json of the response is the merge of both mocked configurations.
        """
        def side_effect(key, default=None):
            if key == "MFE_CONFIG":
                return {"EXAMPLE_VAR": "value", "OTHER": "other"}
            if key == "MFE_CONFIG_OVERRIDES":
                return {"mymfe": {"EXAMPLE_VAR": "mymfe_value"}}
            return default
        configuration_helpers_mock.get_value.side_effect = side_effect

        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        calls = [call("MFE_CONFIG", settings.MFE_CONFIG),
                 call("MFE_CONFIG_OVERRIDES", settings.MFE_CONFIG_OVERRIDES)]
        configuration_helpers_mock.get_value.assert_has_calls(calls)
        self.assertEqual(
            response.json(), {"EXAMPLE_VAR": "mymfe_value", "OTHER": "other", **default_base_config}
        )

    @ddt.unpack
    @ddt.data(
        dict(
            mfe_config={},
            mfe_config_overrides={},
            expected_response={**default_base_config},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={},
            expected_response={"EXAMPLE_VAR": "value", **default_base_config},
        ),
        dict(
            mfe_config={},
            mfe_config_overrides={"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
            expected_response={"EXAMPLE_VAR": "mymfe_value", **default_base_config},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
            expected_response={"EXAMPLE_VAR": "mymfe_value", **default_base_config},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value", "OTHER": "other"},
            mfe_config_overrides={"mymfe": {"EXAMPLE_VAR": "mymfe_value"}},
            expected_response={"EXAMPLE_VAR": "mymfe_value", "OTHER": "other", **default_base_config},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={"yourmfe": {"EXAMPLE_VAR": "yourmfe_value"}},
            expected_response={"EXAMPLE_VAR": "value", **default_base_config},
        ),
        dict(
            mfe_config={"EXAMPLE_VAR": "value"},
            mfe_config_overrides={
                "yourmfe": {"EXAMPLE_VAR": "yourmfe_value"},
                "mymfe": {"EXAMPLE_VAR": "mymfe_value"},
            },
            expected_response={"EXAMPLE_VAR": "mymfe_value", **default_base_config},
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
        def side_effect(key, default=None):
            if key == "MFE_CONFIG":
                return mfe_config
            if key == "MFE_CONFIG_OVERRIDES":
                return mfe_config_overrides
            return default
        configuration_helpers_mock.get_value.side_effect = side_effect

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
        self.assertEqual(response.json(), settings.MFE_CONFIG | default_base_config)

    def test_get_mfe_config_with_queryparam_from_django_settings(self):
        """Test that when there is no site configuration, the API with queryparam takes the django settings.

        Expected result:
        - The status of the response of the request is a HTTP_200_OK.
        - The json response is equal to MFE_CONFIG merged with MFE_CONFIG_OVERRIDES['mymfe']
        """
        response = self.client.get(f"{self.mfe_config_api_url}?mfe=mymfe")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = settings.MFE_CONFIG | settings.MFE_CONFIG_OVERRIDES["mymfe"] | default_base_config
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

    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    def test_get_mfe_config_for_catalog(self, configuration_helpers_mock):
        """Test the mfe config by explicitly using catalog mfe as an example.

        Expected result:
        - The configuration_helpers get_value is called for each catalog-specific configuration.
        - The catalog-specific values are included in the response.
        """
        mfe_config = {"BASE_URL": "https://catalog.example.com", "course_about_twitter_account": "@TestAccount"}
        mfe_config_overrides = {
            "catalog": {
                "SOME_SETTING": "catalog_value",
                "is_cosmetic_price_enabled": True,
                "courses_are_browsable": False,
            }
        }

        def side_effect(key, default=None):
            if key == "MFE_CONFIG":
                return mfe_config
            if key == "MFE_CONFIG_OVERRIDES":
                return mfe_config_overrides
            if key == "ENABLE_COURSE_SORTING_BY_START_DATE":
                return True
            if key == "show_homepage_promo_video":
                return True
            if key == "homepage_promo_video_youtube_id":
                return "test-youtube-id"
            if key == "HOMEPAGE_COURSE_MAX":
                return 8
            return default

        configuration_helpers_mock.get_value.side_effect = side_effect

        response = self.client.get(f"{self.mfe_config_api_url}?mfe=catalog")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data["BASE_URL"], "https://catalog.example.com")
        self.assertEqual(data["SOME_SETTING"], "catalog_value")
        self.assertEqual(data["enable_course_sorting_by_start_date"], True)
        self.assertEqual(data["show_homepage_promo_video"], True)
        self.assertEqual(data["homepage_promo_video_youtube_id"], "test-youtube-id")
        self.assertEqual(data["homepage_course_max"], 8)
        self.assertEqual(data["course_about_twitter_account"], "@TestAccount")
        self.assertEqual(data["is_cosmetic_price_enabled"], True)
        self.assertEqual(data["courses_are_browsable"], False)

    @patch("lms.djangoapps.mfe_config_api.views.configuration_helpers")
    def test_config_order_of_precedence(self, configuration_helpers_mock):
        """Test the precedence of configuration values by explicitly using catalog MFE as an example.

        Expected result:
        - Values should be taken in this order (highest to lowest precedence):
            1. MFE_CONFIG_OVERRIDES from site conf
            2. MFE_CONFIG_OVERRIDES from settings
            3. MFE_CONFIG from site conf
            4. MFE_CONFIG from settings
            5. Plain site configuration
            6. Plain settings
        """
        mfe_config = {
            "homepage_course_max": 10,
            "enable_course_sorting_by_start_date": False,
            "preserved_setting": "preserved"
        }
        mfe_config_overrides = {
            "catalog": {
                "homepage_course_max": 15,
            }
        }

        def side_effect(key, default=None):
            if key == "MFE_CONFIG":
                return mfe_config
            if key == "MFE_CONFIG_OVERRIDES":
                return mfe_config_overrides
            if key == "HOMEPAGE_COURSE_MAX":
                return 5  # Plain site configuration
            if key == "homepage_promo_video_youtube_id":
                return "site-conf-youtube-id"
            return default

        configuration_helpers_mock.get_value.side_effect = side_effect

        with override_settings(
            HOMEPAGE_COURSE_MAX=3,  # Plain settings (lowest precedence)
            FEATURES={'ENABLE_COURSE_SORTING_BY_START_DATE': True}  # Settings FEATURES
        ):
            response = self.client.get(f"{self.mfe_config_api_url}?mfe=catalog")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # MFE_CONFIG_OVERRIDES from site conf (highest precedence)
        self.assertEqual(data["homepage_course_max"], 15)

        # MFE_CONFIG from site conf takes precedence over plain site configuration and settings
        self.assertEqual(data["enable_course_sorting_by_start_date"], False)

        # Plain site configuration takes precedence over plain settings
        self.assertEqual(data["homepage_promo_video_youtube_id"], "site-conf-youtube-id")

        # Value in original MFE_CONFIG not overridden by catalog config should be preserved
        self.assertEqual(data["preserved_setting"], "preserved")
