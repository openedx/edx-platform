"""Unit tests for third_party_auth/pipeline.py."""


import json
import unittest

import ddt
import mock

from lms.djangoapps.program_enrollments.management.commands.tests.utils import UserSocialAuthFactory
from third_party_auth import pipeline
from third_party_auth.tests import testutil
from third_party_auth.tests.specs.base import IntegrationTestMixin
from third_party_auth.tests.specs.test_testshib import SamlIntegrationTestUtilities
from third_party_auth.tests.testutil import simulate_running_pipeline


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
@ddt.ddt
class ProviderUserStateTestCase(testutil.TestCase):
    """Tests ProviderUserState behavior."""

    def test_get_unlink_form_name(self):
        google_provider = self.configure_google_provider(enabled=True)
        state = pipeline.ProviderUserState(google_provider, object(), None)
        self.assertEqual(google_provider.provider_id + '_unlink_form', state.get_unlink_form_name())

    @ddt.data(
        ('saml', 'tpa-saml'),
        ('oauth', 'google-oauth2'),
    )
    @ddt.unpack
    def test_get_idp_logout_url_from_running_pipeline(self, idp_type, backend_name):
        """
        Test idp logout url setting for running pipeline
        """
        self.enable_saml()
        idp_slug = "test"
        idp_config = {"logout_url": "http://example.com/logout"}
        getattr(self, 'configure_{idp_type}_provider'.format(idp_type=idp_type))(
            enabled=True,
            name="Test Provider",
            slug=idp_slug,
            backend_name=backend_name,
            other_settings=json.dumps(idp_config)
        )
        request = mock.MagicMock()
        kwargs = {
            "response": {
                "idp_name": idp_slug
            }
        }
        with simulate_running_pipeline("third_party_auth.pipeline", backend_name, **kwargs):
            logout_url = pipeline.get_idp_logout_url_from_running_pipeline(request)
            self.assertEqual(idp_config['logout_url'], logout_url)


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
@ddt.ddt
class PipelineOverridesTest(SamlIntegrationTestUtilities, IntegrationTestMixin, testutil.SAMLTestCase):
    """
    Tests for pipeline overrides
    """

    def setUp(self):
        super(PipelineOverridesTest, self).setUp()
        self.enable_saml()
        self.provider = self.configure_saml_provider(
            enabled=True,
            name="Test Provider",
            slug='test',
            backend_name='tpa-saml'
        )

    @ddt.data(
        ('S', 'S9fe2', False),
        ('S', 'S9fe2', True),
        ('S.K', 'S_K', False),
        ('S.K.', 'S_K_', False),
        ('S.K.', 'S_K_9fe2', True),
        ('usernamewithcharacterlengthofmorethan30chars', 'usernamewithcharacterlengthofm', False),
        ('usernamewithcharacterlengthofmorethan30chars', 'usernamewithcharacterlengt9fe2', True),
    )
    @ddt.unpack
    @mock.patch('third_party_auth.pipeline.user_exists')
    def test_get_username_in_pipeline(self, idp_username, expected_username, already_exists, mock_user_exists):
        """
        Test get_username method of running pipeline
        """
        details = {
            "username": idp_username,
            "email": "test@example.com"
        }
        mock_user_exists.side_effect = [already_exists, False]
        __, strategy = self.get_request_and_strategy()
        with mock.patch('third_party_auth.pipeline.uuid4') as mock_uuid:
            uuid4 = mock.Mock()
            type(uuid4).hex = mock.PropertyMock(return_value='9fe2c4e93f654fdbb24c02b15259716c')
            mock_uuid.return_value = uuid4
            final_username = pipeline.get_username(strategy, details, self.provider.backend_class())
            self.assertEqual(expected_username, final_username['username'])


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class PipelineLoginAnalyticsTest(IntegrationTestMixin, testutil.TestCase):
    """
    Tests for login_analytics step in the TPA pipeline.
    """

    def setUp(self):
        super(PipelineLoginAnalyticsTest, self).setUp()
        self.provider = self.configure_dummy_provider(
            enabled=True,
            name="Test Dummy Provider",
            slug='test',
            backend_name='dummy'
        )

    def test_tpa_login_tracking_event(self):
        """
        Test successful third party auth login produces correct tracking log event.
        """
        dummy_extra_data = {"foo_extra_1": "something", "foo_extra_2": "something else"}
        social = UserSocialAuthFactory.create(slug=self.provider.slug)
        user = social.user
        uid = social.uid
        social.extra_data = dummy_extra_data
        social.save()
        expected_track_data = {
            'user_id': user.id,
            'username': user.username,
            'auth_data': {
                'tpa_auth_entry': pipeline.AUTH_ENTRY_LOGIN,
                'tpa_provider': 'dummy',
                'tpa_social_uid': uid,
                'tpa_social_extra_data': dummy_extra_data
            }
        }
        expected_segment_track_props = {
            'category': "conversion",
            'label': None,
            'provider': 'dummy'
        }

        __, strategy = self.get_request_and_strategy()
        pipeline_kws = {'uid': social.uid, 'user': user, 'social': social}

        # don't decorate whole test method with these since they can be called creating UserSocialAuth
        with mock.patch("third_party_auth.pipeline.tracker.emit") as mock_tracker_emit:
            with mock.patch("third_party_auth.pipeline.segment.track") as mock_segment_track:
                pipeline.login_analytics(
                    strategy=strategy, backend=self.provider.backend_class(),
                    pipeline_index=0, auth_entry='login', **pipeline_kws
                )
                mock_tracker_emit.assert_called_once_with(name='edx.user.account.authenticated', data=expected_track_data)
                mock_segment_track.assert_called_once_with(
                    user.id, 'edx.bi.user.account.authenticated',
                    expected_segment_track_props
                )
