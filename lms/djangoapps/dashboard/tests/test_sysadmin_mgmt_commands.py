"""
Tests for the Mgmt Commands Feature on the Sysadmin page
"""
import json
from mock import patch
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse

from dashboard.tests.test_sysadmin import SysadminBaseTestCase


@unittest.skipUnless(
    settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'),
    'ENABLE_SYSADMIN_DASHBOARD not set',
)
class TestSysadminMgmtCommands(SysadminBaseTestCase):
    """Tests all code paths in Sysadmin Mgmt Commands"""

    def setUp(self):
        super(TestSysadminMgmtCommands, self).setUp()
        self._setsuperuser_login()
        self.post_params = {
            'command': 'fake_command',
            'key1': 'value1',
            'key2': 'value2',
            'kwflags': ['kwflag1', 'kwflag2'],
            'args': ['arg1', 'arg2'],
        }

    def test_mgmt_commands_handles_systemexit(self):
        with patch('dashboard.sysadmin.call_command') as call_command:
            call_command.side_effect = SystemExit()
            response = self.client.post(reverse('sysadmin_mgmt_commands'), self.post_params)
            self.assertEqual('Command failed', json.loads(response.content.decode('utf-8'))['error'])

    def test_mgmt_commands_handles_exception(self):
        with patch('dashboard.sysadmin.call_command') as call_command:
            call_command.side_effect = Exception('Unknown exception')
            response = self.client.post(reverse('sysadmin_mgmt_commands'), self.post_params)
            self.assertEqual('Unknown exception', json.loads(response.content.decode('utf-8'))['error'])

    def test_mgmt_commands_correct_arguments(self):
        with patch('dashboard.sysadmin.call_command') as call_command:
            self.client.post(reverse('sysadmin_mgmt_commands'), self.post_params)
            call_command.assert_called_with('fake_command', 'arg1', 'arg2', key1='value1', key2='value2', kwflag1=None, kwflag2=None)
