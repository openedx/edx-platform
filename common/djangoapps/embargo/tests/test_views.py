"""Tests for embargo app views. """

import unittest
from mock import patch
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from mako.exceptions import TopLevelLookupException
import ddt

from util.testing import UrlResetMixin
from embargo import messages


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class CourseAccessMessageViewTest(UrlResetMixin, TestCase):
    """Tests for the courseware access message view.

    These end-points serve static content.
    While we *could* check the text on each page,
    this will require changes to the test every time
    the text on the page changes.

    Instead, we load each page we expect to be available
    (based on the configuration in `embargo.messages`)
    and verify that we get the correct status code.

    This will catch errors in the message configuration
    (for example, moving a template and forgetting to
    update the configuration appropriately).

    """

    @patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(CourseAccessMessageViewTest, self).setUp('embargo')

    @ddt.data(*messages.ENROLL_MESSAGES.keys())
    def test_enrollment_messages(self, msg_key):
        self._load_page('enrollment', msg_key)

    @ddt.data(*messages.COURSEWARE_MESSAGES.keys())
    def test_courseware_messages(self, msg_key):
        self._load_page('courseware', msg_key)

    @ddt.data('enrollment', 'courseware')
    def test_invalid_message_key(self, access_point):
        self._load_page(access_point, 'invalid', expected_status=404)

    @patch.dict(settings.FEATURES, {'USE_CUSTOM_THEME': True})
    @ddt.data('enrollment', 'courseware')
    def test_custom_theme_override(self, access_point):
        # Custom override specified for the "embargo" message
        # for backwards compatibility with previous versions
        # of the embargo app.
        # This template isn't available by default, but we can at least
        # verify that the view will look for it when the USE_CUSTOM_THEME
        # feature flag is specified.
        with self.assertRaisesRegexp(TopLevelLookupException, 'static_templates/theme-embargo.html'):
            self._load_page(access_point, 'embargo')

    @patch.dict(settings.FEATURES, {'USE_CUSTOM_THEME': True})
    @ddt.data('enrollment', 'courseware')
    def test_custom_theme_override_not_specified(self, access_point):
        # No custom override specified for the "default" message
        self._load_page(access_point, 'default')

    def _load_page(self, access_point, message_key, expected_status=200):
        """Load the message page and check the status code. """
        url = reverse('embargo_blocked_message', kwargs={
            'access_point': access_point,
            'message_key': message_key
        })
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, expected_status,
            msg=(
                u"Unexpected status code when loading '{url}': "
                u"expected {expected} but got {actual}"
            ).format(
                url=url,
                expected=expected_status,
                actual=response.status_code
            )
        )
