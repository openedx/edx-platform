""" unittests for strategy.py """
import unittest
import ddt
import mock

from django.test import TestCase

from third_party_auth.strategy import ConfigurationModelStrategy
from third_party_auth.tests import testutil


@ddt.ddt
@mock.patch('student.views.create_account_with_params')
@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class TestStrategy(TestCase):
    """ Unit tests for authentication strategy """
    def setUp(self):
        super(TestStrategy, self).setUp()
        self.request_mock = mock.Mock()
        self.strategy = ConfigurationModelStrategy(mock.Mock(), request=self.request_mock)

    def _get_last_call_args(self, patched_create_account):
        """ Helper to get last call arguments from a mock """
        args, unused_kwargs = patched_create_account.call_args
        return args

    @ddt.data(
        (True, None, 'host', 'host'),
        (True, "", 'other_host', 'other_host'),
        (True, 'x_forwarded_host', 'irrelevant', 'x_forwarded_host'),
        (True, 'other_x_forwarded_host', 'still_irrelevant', 'other_x_forwarded_host'),
        (False, None, 'host', 'host'),
        (False, "", 'other_host', 'other_host'),
        (False, 'x_forwarded_host', 'normal_host', 'normal_host'),
        (False, 'other_x_forwarded_host', 'other_normal_host', 'other_normal_host'),
    )
    @ddt.unpack
    def test_request_host(self, respect_x_headers, x_forwarded_value, get_host_value, expected_value, unused_patch):
        self.request_mock.META = {}
        self.request_mock.get_host.return_value = get_host_value
        if x_forwarded_value is not None:
            self.request_mock.META['HTTP_X_FORWARDED_HOST'] = x_forwarded_value

        with self.settings(RESPECT_X_FORWARDED_HEADERS=respect_x_headers):
            self.assertEqual(self.strategy.request_host(), expected_value)

    @ddt.data(
        (True, None, 'port', 'port'),
        (True, "", 'other_port', 'other_port'),
        (True, 'x_forwarded_port', 'irrelevant', 'x_forwarded_port'),
        (True, 'other_x_forwarded_port', 'still_irrelevant', 'other_x_forwarded_port'),
        (False, None, 'port', 'port'),
        (False, "", 'other_port', 'other_port'),
        (False, 'x_forwarded_port', 'normal_port', 'normal_port'),
        (False, 'other_x_forwarded_port', 'other_normal_port', 'other_normal_port'),
    )
    @ddt.unpack
    def test_request_port(self, respect_x_headers, x_forwarded_value, server_port_value, expected_value, unused_patch):
        self.request_mock.META = {'SERVER_PORT': server_port_value}
        if x_forwarded_value is not None:
            self.request_mock.META['HTTP_X_FORWARDED_PORT'] = x_forwarded_value

        with self.settings(RESPECT_X_FORWARDED_HEADERS=respect_x_headers):
            self.assertEqual(self.strategy.request_port(), expected_value)
