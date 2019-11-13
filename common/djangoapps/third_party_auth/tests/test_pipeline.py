"""Unit tests for third_party_auth/pipeline.py."""

from __future__ import absolute_import

import unittest

import mock
from django.test import TestCase
from django.test.utils import override_settings

from student.tests.factories import UserFactory
from third_party_auth import pipeline
from third_party_auth.tests import testutil


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class ProviderUserStateTestCase(testutil.TestCase):
    """Tests ProviderUserState behavior."""

    def test_get_unlink_form_name(self):
        google_provider = self.configure_google_provider(enabled=True)
        state = pipeline.ProviderUserState(google_provider, object(), None)
        self.assertEqual(google_provider.provider_id + '_unlink_form', state.get_unlink_form_name())


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class EnsureEnterpriseCustomerActiveStatusTestCase(testutil.TestCase, TestCase):
    """Tests ensuring that we are only updating learner enterprise customer when it is needed."""

    def setUp(self):
        super(EnsureEnterpriseCustomerActiveStatusTestCase, self).setUp()
        self.idp_name = 'tpa-saml'
        self.user = UserFactory.create()
        self.response = {'idp_name': 'default'}
        self.backend = mock.MagicMock()
        self.backend.name = self.idp_name

    @mock.patch('openedx.features.enterprise_support.api.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.api.get_enterprise_learner_data')
    @override_settings(FEATURES=dict(ENABLE_ENTERPRISE_INTEGRATION=True))
    def test_enterprise_customer_learner_status(self, mock_get_enterprise, mock_post_enterprise_customer):
        enterprise_learner_data = [
            {'enterprise_customer': {'uuid': 'ab12', 'identity_provider': 'saml-default'}},
            {'enterprise_customer': {'uuid': 'cd34', 'identity_provider': 'saml-demo'}}

        ]
        mock_get_enterprise.return_value = enterprise_learner_data
        pipeline.set_learner_active_enterprise(self.user, self.backend, self.response)
        mock_get_enterprise.assert_called_once()
        mock_post_enterprise_customer.return_value = None
        self.assertFalse(mock_post_enterprise_customer.called)

    @mock.patch('openedx.features.enterprise_support.api.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.api.get_enterprise_learner_data')
    @override_settings(FEATURES=dict(ENABLE_ENTERPRISE_INTEGRATION=True))
    def test_update_enterprise_customer_learner_status(self, mock_get_enterprise, mock_post_enterprise_customer):
        enterprise_learner_data = [
            {'enterprise_customer': {'uuid': 'cd34', 'identity_provider': 'saml-demo'}},
            {'enterprise_customer': {'uuid': 'ab12', 'identity_provider': 'saml-default'}}
        ]
        mock_get_enterprise.return_value = enterprise_learner_data
        pipeline.set_learner_active_enterprise(self.user, self.backend, self.response)
        mock_get_enterprise.assert_called_once()
        mock_post_enterprise_customer.return_value = None
        mock_post_enterprise_customer.assert_called_once()
