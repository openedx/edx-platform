"""
Tests related to the basic footer-switching based off SITE_NAME to ensure
edx.org uses an edx footer but other instances use an Open edX footer.
"""

from django.test import TestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class TestFooter(TestCase):
    """
    Tests for edx and OpenEdX footer
    """

    SOCIAL_MEDIA_NAMES = [
        "facebook",
        "instagram",
        "twitter",
        "linkedin",
        "tumblr",
        "meetup",
        "reddit",
        "youtube",
    ]

    SOCIAL_MEDIA_URLS = {
        "facebook": "http://www.facebook.com/",
        "instagram": "https://instagram.com/",
        "twitter": "https://twitter.com/",
        "linkedin": "http://www.linkedin.com/",
        "tumblr": "http://www.tumblr.com/",
        "meetup": "http://www.meetup.com/",
        "reddit": "http://www.reddit.com/",
        "youtube": "https://www.youtube.com/"
    }

    def test_openedx_footer(self):
        """
        Verify that the homepage, when accessed at something other than
        edx.org, has the Open edX footer
        """
        resp = self.client.get('/')
        assert resp.status_code == 200
        self.assertContains(resp, 'footer-openedx')
