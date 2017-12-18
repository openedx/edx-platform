""" Unit tests for custom UserProfile properties. """

import ddt

from django.test import TestCase
from openedx.core.djangolib.testing.utils import skip_unless_lms

from ..utils import validate_social_link, format_social_link


@ddt.ddt
class UserAccountSettingsTest(TestCase):
    """Unit tests for setting Social Media Links."""

    def setUp(self):
        super(UserAccountSettingsTest, self).setUp()

    def validate_social_link(self, social_platform, link):
        """
        Helper method that returns True if the social link is valid, False if
        the input link fails validation and will throw an error.
        """
        try:
            validate_social_link(social_platform, link)
        except ValueError:
            return False
        return True

    @ddt.data(
        ('facebook', 'www.facebook.com/edX', 'https://www.facebook.com/edX', True),
        ('facebook', 'facebook.com/edX/', 'https://www.facebook.com/edX', True),
        ('facebook', 'HTTP://facebook.com/edX/', 'https://www.facebook.com/edX', True),
        ('facebook', 'www.evilwebsite.com/123', None, False),
        ('twitter', 'https://www.twiter.com/edX/', None, False),
        ('twitter', 'https://www.twitter.com/edX/123s', None, False),
        ('twitter', 'twitter.com/edX', 'https://www.twitter.com/edX', True),
        ('twitter', 'twitter.com/edX?foo=bar', 'https://www.twitter.com/edX', True),
        ('twitter', 'twitter.com/test.user', 'https://www.twitter.com/test.user', True),
        ('linkedin', 'www.linkedin.com/harryrein', None, False),
        ('linkedin', 'www.linkedin.com/in/harryrein-1234', 'https://www.linkedin.com/in/harryrein-1234', True),
        ('linkedin', 'www.evilwebsite.com/123?www.linkedin.com/edX', None, False),
        ('linkedin', '', '', True),
        ('linkedin', None, None, False),
    )
    @ddt.unpack
    @skip_unless_lms
    def test_social_link_input(self, platform_name, link_input, formatted_link_expected, is_valid_expected):
        """
        Verify that social links are correctly validated and formatted.
        """
        self.assertEqual(is_valid_expected, self.validate_social_link(platform_name, link_input))

        self.assertEqual(formatted_link_expected, format_social_link(platform_name, link_input))
