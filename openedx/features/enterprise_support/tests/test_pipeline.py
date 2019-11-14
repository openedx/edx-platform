"""
Tests for SAML Enterprise Pipeline.
"""

from __future__ import absolute_import

import mock
from django.test import TestCase
from django.test.utils import override_settings
from student.tests.factories import UserFactory

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support import pipeline
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED


@override_settings(FEATURES=FEATURES_WITH_ENTERPRISE_ENABLED)
@skip_unless_lms
class EnsureEnterpriseCustomerActiveStatusTestCase(TestCase):
    """Tests ensuring that we are only updating learner enterprise_customer when it is needed."""

    def setUp(self):
        super(EnsureEnterpriseCustomerActiveStatusTestCase, self).setUp()
        self.user = UserFactory.create()
        self.strategy = mock.MagicMock()
        self.request = mock.MagicMock(session={'enterprise_customer': {'identity_provider': 'saml-default'}})
        self.strategy.request = self.request
        self.backend = mock.MagicMock()
        self.backend.name = 'tpa-saml'
        self.saml_provider = mock.MagicMock(
            slug='unique_slug',
            send_to_registration_first=True,
            skip_email_verification=True
        )

    @mock.patch('openedx.features.enterprise_support.pipeline.is_multiple_user_enterprises_feature_enabled')
    @mock.patch('openedx.features.enterprise_support.pipeline.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.pipeline.get_enterprise_learner_data')
    def test_enterprise_customer_in_session(self, mock_get_enterprise, mock_post_enterprise_customer,
                                            mocked_multiple_enterprises_feature):
        with mock.patch('third_party_auth.pipeline.provider.Registry.get_from_pipeline') as get_from_pipeline:
            get_from_pipeline.return_value = self.saml_provider
            with mock.patch(
                'third_party_auth.pipeline.provider.Registry.get_enabled_by_backend_name'
            ) as enabled_saml_providers:
                mocked_multiple_enterprises_feature.return_value = True
                kwargs = {'response': {'idp_name': 'default'}}
                enabled_saml_providers.return_value = [self.saml_provider, ]
                pipeline.set_learner_active_enterprise(self.user, self.backend, self.strategy, **kwargs)
                self.assertFalse(mock_get_enterprise.called)
                self.assertFalse(mock_post_enterprise_customer.called)

    @mock.patch('openedx.features.enterprise_support.pipeline.is_multiple_user_enterprises_feature_enabled')
    @mock.patch('openedx.features.enterprise_support.pipeline.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.pipeline.get_enterprise_learner_data')
    def test_update_enterprise_customer_status(self, mock_get_enterprise, mock_post_enterprise_customer,
                                               mocked_multiple_enterprises_feature):
        kwargs = {'response': {'idp_name': 'demo'}}
        enterprise_learner_data = [
            {'enterprise_customer': {'uuid': 'ab12', 'identity_provider': 'saml-default'}},
            {'enterprise_customer': {'uuid': 'cd34', 'identity_provider': 'saml-demo'}}
        ]

        with mock.patch('third_party_auth.pipeline.provider.Registry.get_from_pipeline') as get_from_pipeline:
            get_from_pipeline.return_value = self.saml_provider
            with mock.patch(
                'third_party_auth.pipeline.provider.Registry.get_enabled_by_backend_name'
            ) as enabled_saml_providers:
                mocked_multiple_enterprises_feature.return_value = True
                enabled_saml_providers.return_value = [self.saml_provider, ]
                mock_get_enterprise.return_value = enterprise_learner_data
                mock_post_enterprise_customer.return_value = True
                pipeline.set_learner_active_enterprise(self.user, self.backend, self.strategy, **kwargs)
                mock_get_enterprise.assert_called_once()
                mock_post_enterprise_customer.assert_called_once()
                self.assertEqual(self.request.session.get('enterprise_customer'),
                                 enterprise_learner_data[1]['enterprise_customer'])

    @mock.patch('openedx.features.enterprise_support.pipeline.is_multiple_user_enterprises_feature_enabled')
    @mock.patch('openedx.features.enterprise_support.pipeline.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.pipeline.get_enterprise_learner_data')
    def test_failed_update_enterprise_customer_status(self, mock_get_enterprise, mock_post_enterprise_customer,
                                                      mocked_multiple_enterprises_feature):
        kwargs = {'response': {'idp_name': 'demo-test'}}
        enterprise_learner_data = [
            {'enterprise_customer': {'uuid': 'ab12', 'identity_provider': 'saml-default'}},
            {'enterprise_customer': {'uuid': 'cd34', 'identity_provider': 'saml-demo-test'}}
        ]

        with mock.patch('third_party_auth.pipeline.provider.Registry.get_from_pipeline') as get_from_pipeline:
            get_from_pipeline.return_value = self.saml_provider
            with mock.patch(
                'third_party_auth.pipeline.provider.Registry.get_enabled_by_backend_name'
            ) as enabled_saml_providers:
                mocked_multiple_enterprises_feature.return_value = True
                enabled_saml_providers.return_value = [self.saml_provider, ]
                mock_get_enterprise.return_value = enterprise_learner_data
                mock_post_enterprise_customer.return_value = False
                pipeline.set_learner_active_enterprise(self.user, self.backend, self.strategy, **kwargs)
                mock_get_enterprise.assert_called_once()
                mock_post_enterprise_customer.assert_called_once()
                self.assertNotEqual(self.request.session.get('enterprise_customer'),
                                    enterprise_learner_data[1]['enterprise_customer'])

    @mock.patch('openedx.features.enterprise_support.pipeline.is_multiple_user_enterprises_feature_enabled')
    @mock.patch('openedx.features.enterprise_support.pipeline.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.pipeline.get_enterprise_learner_data')
    def test_with_one_enterprise_customer(self, mock_get_enterprise, mock_post_enterprise_customer,
                                          mocked_multiple_enterprises_feature):
        kwargs = {'response': {'idp_name': 'demo-test'}}
        enterprise_learner_data = [
            {'enterprise_customer': {'uuid': 'cd34', 'identity_provider': 'saml-demo-test'}}
        ]

        with mock.patch('third_party_auth.pipeline.provider.Registry.get_from_pipeline') as get_from_pipeline:
            get_from_pipeline.return_value = self.saml_provider
            with mock.patch(
                'third_party_auth.pipeline.provider.Registry.get_enabled_by_backend_name'
            ) as enabled_saml_providers:
                mocked_multiple_enterprises_feature.return_value = True
                enabled_saml_providers.return_value = [self.saml_provider, ]
                mock_get_enterprise.return_value = enterprise_learner_data
                mock_post_enterprise_customer.return_value = False
                pipeline.set_learner_active_enterprise(self.user, self.backend, self.strategy, **kwargs)
                mock_get_enterprise.assert_called_once()
                self.assertFalse(mock_post_enterprise_customer.called)

    @mock.patch('openedx.features.enterprise_support.pipeline.is_multiple_user_enterprises_feature_enabled')
    @mock.patch('openedx.features.enterprise_support.pipeline.EnterpriseApiClient.post_active_enterprise_customer')
    @mock.patch('openedx.features.enterprise_support.pipeline.get_enterprise_learner_data')
    def test_with_multiple_user_enterprises_featured_disabled(self, mock_get_enterprise, mock_post_enterprise_customer,
                                                              mocked_multiple_enterprises_feature):
        kwargs = {'response': {'idp_name': 'demo-test'}}
        enterprise_learner_data = [
            {'enterprise_customer': {'uuid': 'cd34', 'identity_provider': 'saml-demo-test'}}
        ]

        with mock.patch('third_party_auth.pipeline.provider.Registry.get_from_pipeline') as get_from_pipeline:
            get_from_pipeline.return_value = self.saml_provider
            with mock.patch(
                'third_party_auth.pipeline.provider.Registry.get_enabled_by_backend_name'
            ) as enabled_saml_providers:
                mocked_multiple_enterprises_feature.return_value = False
                enabled_saml_providers.return_value = [self.saml_provider, ]
                mock_get_enterprise.return_value = enterprise_learner_data
                mock_post_enterprise_customer.return_value = False
                pipeline.set_learner_active_enterprise(self.user, self.backend, self.strategy, **kwargs)
                self.assertFalse(mock_get_enterprise.called)
                self.assertFalse(mock_post_enterprise_customer.called)
