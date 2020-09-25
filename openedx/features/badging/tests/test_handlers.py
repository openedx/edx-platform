"""
Unit tests for badging handlers
"""
from django.test import TestCase
from edx_notifications.lib.publisher import get_notification_type

from openedx.features.badging.constants import EARNED_BADGE_NOTIFICATION_TYPE, JSON_NOTIFICATION_RENDERER

from ..handlers import register_notification_types


class BadgeHandlerTestCase(TestCase):

    def test_register_notification_types(self):
        """
        Test that notification type is registered correctly
        :return: None
        """
        # register badge notification type
        register_notification_types(None)

        badge_notification_type = get_notification_type(EARNED_BADGE_NOTIFICATION_TYPE)

        self.assertEqual(badge_notification_type.name, EARNED_BADGE_NOTIFICATION_TYPE)
        self.assertEqual(badge_notification_type.renderer, JSON_NOTIFICATION_RENDERER)
