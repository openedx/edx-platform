"""
Tests for the Django management command force_send_digest
"""

import mock
from django.conf import settings
from django.test import TestCase
from student.management.commands import force_send_notification_digest


@mock.patch.dict(settings.FEATURES, {'ENABLE_NOTIFICATIONS': True})
class ForceSendDigestCommandTest(TestCase):
    def test_command_all(self):
        # run the management command for sending notification digests.
        force_send_notification_digest.Command().handle(**{'send_daily_digest': True, 'send_weekly_digest': True, 'namespace': 'All'})

    def test_command_namespaced(self):
        # run the management command for sending notification digests.
        force_send_notification_digest.Command().handle(**{'send_daily_digest': True, 'send_weekly_digest': True, 'namespace': 'ABC'})
