# -*- coding: utf-8 -*-
"""
Tests django_sudo_helpers templatetags to create third party auth links.
"""
import unittest
from mock import patch
from django.conf import settings
from social.apps.django_app.default import models as social_models
from django.test.client import RequestFactory

from student.helpers import auth_pipeline_urls, get_next_url_for_login_page
from django_sudo_helpers.tests import utils
from third_party_auth.tests import testutil
from third_party_auth.pipeline import AUTH_ENTRY_SUDO
from django_sudo_helpers.templatetags import third_party_auth_links


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
@unittest.skipUnless(utils.DJANGO_SUDO_FEATURE_ENABLED, 'django-sudo not enabled')
class ThirdPartyAuthLinkTests(testutil.TestCase):
    """
    Make sure some of the templatetags work.
    """
    def setUp(self):
        """
        Test third party auth links.
        """
        super(ThirdPartyAuthLinkTests, self).setUp()
        self.user = social_models.DjangoStorage.user.create_user(username='username', password='password')
        self.url = '/course_team/edx/111/q2'
        self.request = RequestFactory().get(self.url)

    @patch.dict(settings.FEATURES, {'ENABLE_THIRD_PARTY_AUTH': False})
    def test_third_party_auth_links_disabled(self):
        """
        Test that response is empty when third party auth is disabled.
        """
        self.assertEqual(settings.FEATURES["ENABLE_THIRD_PARTY_AUTH"], False)
        self.request.user = self.user
        response = third_party_auth_links.third_party_auth_links({'request': self.request})
        self.assertEqual(response, '')

    @patch.dict(settings.FEATURES, {'ENABLE_THIRD_PARTY_AUTH': True})
    def test_third_party_auth_links_enabled(self):
        """
        Test that response has buttons when third party auth is enabled for google and linkedin.
        """
        self.assertEqual(settings.FEATURES["ENABLE_THIRD_PARTY_AUTH"], True)
        # Get and enable providers.
        google_provider = self.configure_google_provider(enabled=True)
        linkedin_provider = self.configure_linkedin_provider(enabled=True)

        # Link provides to user account.
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', google_provider.backend_name)
        social_models.DjangoStorage.user.create_social_auth(self.user, 'uid', linkedin_provider.backend_name)

        self.request.user = self.user
        response = third_party_auth_links.third_party_auth_links({'request': self.request})

        redirect_to = get_next_url_for_login_page(self.request)
        pipeline_url = auth_pipeline_urls(AUTH_ENTRY_SUDO, redirect_url=redirect_to)
        # Assert that button classes are present in response for enabled providers.
        self.assertIn(pipeline_url['oa2-google-oauth2'].replace('&', '&amp;'), response)
        self.assertIn(pipeline_url['oa2-linkedin-oauth2'].replace('&', '&amp;'), response)
