"""
Test lms startup
"""

from django.conf import settings
from django.test import TestCase

from mock import patch
from lms.startup import run


class StartupTestCase(TestCase):
    """
    Test lms startup
    """

    def setUp(self):
        super(StartupTestCase, self).setUp()

    @patch.dict("django.conf.settings.FEATURES", {"NOTIFICATIONS_ENABLED": True, "ENABLE_THIRD_PARTY_AUTH": False})
    def test_run_with_notifications_enabled(self):
        self.assertEqual(settings.FEATURES["NOTIFICATIONS_ENABLED"], True)
        with patch('lms.startup.startup_notification_subsystem') as mock_notification_subsystem:
            run()
            self.assertTrue(mock_notification_subsystem.called)
