"""Test the Appsembler Analytics context processor module
"""
import hashlib
from mock import Mock, patch, PropertyMock
import ddt

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from openedx.core.djangoapps.appsembler.analytics.context_processors import (
    google_analytics,
    mixpanel,
    hubspot,
)
from student.tests.factories import UserFactory

APPSEMBLER_APP = 'openedx.core.djangoapps.appsembler.analytics'


@ddt.ddt
class GoogleAnalyticsContextProcessorTests(TestCase):

    def setUp(self):
        self.request = Mock()
        self.request.user = UserFactory()

    @patch.object(get_user_model(),
                  'is_authenticated',
                  PropertyMock(return_value=True))
    @patch(APPSEMBLER_APP + '.context_processors.user_has_role',
           return_value=True)
    def test_authorized_user(self, _):
        expected_email_hash = hashlib.sha256(self.request.user.email.encode(
            'utf-8')).hexdigest()
        data = google_analytics(self.request)
        assert data['USER_EMAIL_HASH'] == expected_email_hash

    @ddt.data((False, False), (False, True), (True, False))
    @ddt.unpack
    def test_unauthorized_user(self, is_authenticated, user_has_role):
        with patch.object(get_user_model(),
                          'is_authenticated',
                          PropertyMock(return_value=is_authenticated)):
            with patch(APPSEMBLER_APP + '.context_processors.user_has_role',
                       return_value=user_has_role):
                data = google_analytics(self.request)
        assert 'USER_EMAIL_HASH' not in data

    @ddt.data((None, False), ('foo', True))
    @ddt.unpack
    def test_app_id_show(self, app_id, show_app):
        with override_settings(GOOGLE_ANALYTICS_APP_ID=app_id):
            data = google_analytics(self.request)
            assert data['GOOGLE_ANALYTICS_APP_ID'] == app_id
            assert data['SHOW_GOOGLE_ANALYTICS'] == show_app

    def test_with_no_setting(self):
        data = google_analytics(self.request)
        assert data['GOOGLE_ANALYTICS_APP_ID'] is None
        assert data['SHOW_GOOGLE_ANALYTICS'] is False


@ddt.ddt
class MixpanelContextProcessorTests(TestCase):
    def setUp(self):
        self.request = Mock()

    @ddt.data((None, False), ('foo', True))
    @ddt.unpack
    def test_basic(self, app_id, show_app):
        with override_settings(MIXPANEL_APP_ID=app_id):
            data = mixpanel(self.request)
            assert data['MIXPANEL_APP_ID'] == app_id
            assert data['SHOW_MIXPANEL'] == show_app

    def test_with_no_setting(self):
        data = mixpanel(self.request)
        assert data['MIXPANEL_APP_ID'] is None
        assert data['SHOW_MIXPANEL'] is False


@ddt.ddt
class HubspotContextProcessorTests(TestCase):

    def setUp(self):
        self.request = Mock()

    @override_settings(HUBSPOT_PORTAL_ID='foo')
    def test_basic(self):
        with patch(APPSEMBLER_APP + '.context_processors.should_show_hubspot',
                   return_value=True):
            data = hubspot(self.request)
            assert data['HUBSPOT_PORTAL_ID'] == 'foo'
            assert data['SHOW_HUBSPOT'] is True

    def test_with_no_setting(self):
        data = hubspot(self.request)
        assert data['HUBSPOT_PORTAL_ID'] is None
        assert data['SHOW_HUBSPOT'] is False
