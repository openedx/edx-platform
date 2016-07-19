"""
Tests for helper function provided by site_configuration app.
"""

from django.test import TestCase

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.site_configuration.tests.test_util import (
    with_site_configuration,
    with_site_configuration_context,
)

test_config = {   # pylint: disable=invalid-name
    "university": "Test University",
    "platform_name": "Test Education Program",
    "SITE_NAME": "test.localhost",
    "course_org_filter": "TestX",
    "css_overrides_file": "test/css/site.css",
    "ENABLE_MKTG_SITE": False,
    "ENABLE_THIRD_PARTY_AUTH": False,
    "course_about_show_social_links": False,
    "favicon_path": "/static/test.ico",

    "REGISTRATION_EXTRA_FIELDS": {
        "first_name": "required",
        "last_name": "required",
        "level_of_education": "hidden",
        "gender": "hidden",
        "year_of_birth": "required",
        "mailing_address": "hidden",
        "goals": "hidden",
        "terms_of_service": "required",
        "honor_code": "hidden",
        "state": "required",
        "country": "required"
    },
}


class TestHelpers(TestCase):
    """
    Tests for helper function provided by site_configuration.
    """

    @with_site_configuration(configuration=test_config)
    def test_get_value(self):
        """
        Test that get_value returns correct value for any given key.
        """
        # Make sure entry is saved and retrieved correctly
        self.assertEqual(configuration_helpers.get_value("university"), test_config['university'])
        self.assertEqual(configuration_helpers.get_value("platform_name"), test_config['platform_name'])
        self.assertEqual(configuration_helpers.get_value("SITE_NAME"), test_config['SITE_NAME'])
        self.assertEqual(configuration_helpers.get_value("course_org_filter"), test_config['course_org_filter'])
        self.assertEqual(configuration_helpers.get_value("css_overrides_file"), test_config['css_overrides_file'])
        self.assertEqual(configuration_helpers.get_value("ENABLE_MKTG_SITE"), test_config['ENABLE_MKTG_SITE'])
        self.assertEqual(configuration_helpers.get_value("favicon_path"), test_config['favicon_path'])
        self.assertEqual(
            configuration_helpers.get_value("ENABLE_THIRD_PARTY_AUTH"),
            test_config['ENABLE_THIRD_PARTY_AUTH'],
        )
        self.assertEqual(
            configuration_helpers.get_value("course_about_show_social_links"),
            test_config['course_about_show_social_links'],
        )

        # Test that the default value is returned if the value for the given key is not found in the configuration
        self.assertEqual(
            configuration_helpers.get_value("non_existent_name", "dummy-default-value"),
            "dummy-default-value",
        )

    @with_site_configuration(configuration=test_config)
    def test_get_dict(self):
        """
        Test that get_dict returns correct value for any given key.
        """
        # Make sure entry is saved and retrieved correctly
        self.assertItemsEqual(
            configuration_helpers.get_dict("REGISTRATION_EXTRA_FIELDS"),
            test_config['REGISTRATION_EXTRA_FIELDS'],
        )

        default = {"test1": 123, "first_name": "Test"}
        expected = default
        expected.update(test_config['REGISTRATION_EXTRA_FIELDS'])

        # Test that the default value is returned if the value for the given key is not found in the configuration
        self.assertItemsEqual(
            configuration_helpers.get_dict("REGISTRATION_EXTRA_FIELDS", default),
            expected,
        )

    @with_site_configuration(configuration=test_config)
    def test_has_override_value(self):
        """
        Test that has_override_value returns correct value for any given key.
        """

        self.assertTrue(configuration_helpers.has_override_value("university"))
        self.assertTrue(configuration_helpers.has_override_value("platform_name"))
        self.assertTrue(configuration_helpers.has_override_value("ENABLE_MKTG_SITE"))
        self.assertTrue(configuration_helpers.has_override_value("REGISTRATION_EXTRA_FIELDS"))

        self.assertFalse(configuration_helpers.has_override_value("non_existent_key"))

    def test_is_site_configuration_enabled(self):
        """
        Test that is_site_configuration_enabled returns True when configuration is enabled.
        """
        with with_site_configuration_context(configuration=test_config):
            self.assertTrue(configuration_helpers.is_site_configuration_enabled())

        # Test without a Site Configuration
        self.assertFalse(configuration_helpers.is_site_configuration_enabled())

    def test_get_value_for_org(self):
        """
        Test that get_value_for_org returns correct value for any given key.
        """
        test_org = test_config['course_org_filter']
        with with_site_configuration_context(configuration=test_config):
            self.assertEqual(
                configuration_helpers.get_value_for_org(test_org, "university"),
                test_config['university']
            )
            self.assertEqual(
                configuration_helpers.get_value_for_org(test_org, "css_overrides_file"),
                test_config['css_overrides_file']
            )

            self.assertItemsEqual(
                configuration_helpers.get_value_for_org(test_org, "REGISTRATION_EXTRA_FIELDS"),
                test_config['REGISTRATION_EXTRA_FIELDS']
            )

            # Test default value of key is not present in configuration
            self.assertEqual(
                configuration_helpers.get_value_for_org(test_org, "non_existent_key"),
                None
            )
            self.assertEqual(
                configuration_helpers.get_value_for_org(test_org, "non_existent_key", "default for non existent"),
                "default for non existent"
            )
            self.assertEqual(
                configuration_helpers.get_value_for_org("missing_org", "university", "default for non existent"),
                "default for non existent"
            )

    def test_get_all_orgs(self):
        """
        Test that get_all_orgs returns correct values.
        """
        test_orgs = [test_config['course_org_filter']]
        with with_site_configuration_context(configuration=test_config):
            self.assertItemsEqual(
                list(configuration_helpers.get_all_orgs()),
                test_orgs,
            )
