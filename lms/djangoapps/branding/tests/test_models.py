"""
Tests for the Video Branding configuration.
"""


from django.core.exceptions import ValidationError
from django.test import TestCase

from lms.djangoapps.branding.models import BrandingInfoConfig


class BrandingInfoConfigTest(TestCase):
    """
    Test the BrandingInfoConfig model.
    """

    def setUp(self):
        super(BrandingInfoConfigTest, self).setUp()
        self.configuration_string = """{
            "CN": {
                    "url": "http://www.xuetangx.com",
                    "logo_src": "http://www.xuetangx.com/static/images/logo.png",
                    "logo_tag": "Video hosted by XuetangX.com"
            }
        }"""
        self.config = BrandingInfoConfig(configuration=self.configuration_string)

    def test_create(self):
        """
        Tests creation of configuration.
        """
        self.config.save()
        self.assertEqual(self.config.configuration, self.configuration_string)

    def test_clean_bad_json(self):
        """
        Tests if bad Json string was given.
        """
        self.config = BrandingInfoConfig(configuration='{"bad":"test"')
        self.assertRaises(ValidationError, self.config.clean)

    def test_get(self):
        """
        Tests get configuration from saved string.
        """
        self.config.enabled = True
        self.config.save()
        expected_config = {
            "CN": {
                "url": "http://www.xuetangx.com",
                "logo_src": "http://www.xuetangx.com/static/images/logo.png",
                "logo_tag": "Video hosted by XuetangX.com"
            }
        }
        self.assertEqual(self.config.get_config(), expected_config)

    def test_get_not_enabled(self):
        """
        Tests get configuration that is not enabled.
        """
        self.config.enabled = False
        self.config.save()
        self.assertEqual(self.config.get_config(), {})
