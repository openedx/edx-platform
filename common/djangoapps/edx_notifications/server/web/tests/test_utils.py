"""
Unit tests for utils.py
"""

from django.test import TestCase

from edx_notifications.server.web.utils import get_notifications_widget_context


class TestUtils(TestCase):
    """
    Unit tests for the utils.py file
    """

    def test_get_widget_context(self):
        """
        Make sure we get the render context that we expect
        """

        render_context = get_notifications_widget_context(
            override_context={
                'test_settings': 'ok',
                'global_variables': {
                    'always_show_dates_on_unread': False
                }
            }
        )

        self.assertIn('endpoints', render_context)

        endpoints = render_context['endpoints']
        self.assertIn('unread_notification_count', endpoints)
        self.assertIn('user_notifications_all', endpoints)
        self.assertIn('renderer_templates_urls', endpoints)
        self.assertIn('ok', render_context['test_settings'])

        # make sure nested dictionary overrides work without destroying
        # the base values
        self.assertFalse(render_context['global_variables']['always_show_dates_on_unread'])
        self.assertEquals(render_context['global_variables']['app_name'], 'Your App Name Here')
