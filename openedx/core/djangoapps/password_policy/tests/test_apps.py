"""
Test password policy settings
"""


import datetime
from dateutil.parser import parse as parse_date
from django.conf import settings
from django.test import TestCase, override_settings
from mock import patch

import openedx.core.djangoapps.password_policy as password_policy
from openedx.core.djangoapps.password_policy.apps import PasswordPolicyConfig


class TestApps(TestCase):
    """
    Tests plugin config
    """

    @override_settings(PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG={
        'GENERAL_USER_COMPLIANCE_DEADLINE': '2018-01-01 00:00:00+00:00',
        'STAFF_USER_COMPLIANCE_DEADLINE': 'foo',
    })
    @patch('openedx.core.djangoapps.password_policy.apps.log')
    def test_settings_misconfiguration(self, mock_log):
        """
        Test that we gracefully handle misconfigurations
        """
        app = PasswordPolicyConfig('openedx.core.djangoapps.password_policy', password_policy)
        app.ready()
        config = settings.PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG

        self.assertEqual(mock_log.exception.call_count, 1)
        self.assertIsNone(config['STAFF_USER_COMPLIANCE_DEADLINE'])

        self.assertIsInstance(config['GENERAL_USER_COMPLIANCE_DEADLINE'], datetime.datetime)
        self.assertEqual(config['GENERAL_USER_COMPLIANCE_DEADLINE'], parse_date('2018-01-01 00:00:00+00:00'))
