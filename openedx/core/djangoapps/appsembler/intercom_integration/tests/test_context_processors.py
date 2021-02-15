"""Test the Appsembler Analytics context processor module
"""
import hmac
import hashlib
from mock import Mock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from openedx.core.djangoapps.appsembler.intercom_integration.context_processors import (
    intercom
)

from student.tests.factories import UserFactory

APPSEMBLER_APP = 'openedx.core.djangoapps.appsembler.intercom_integration'


class IntercomContextProcessorTests(TestCase):

    def setUp(self):
        self.request = Mock()
        self.request.user = UserFactory()
        self.request.site.domain = 'example.com'

    @override_settings(INTERCOM_APP_SECRET='setec-astronomy')
    @override_settings(INTERCOM_APP_ID='roger-roger')
    @patch(APPSEMBLER_APP + '.context_processors.should_show_intercom_widget',
           return_value=True)
    def test_authorized_user(self, _):
        expected_user_hash = hmac.new(
            str(settings.INTERCOM_APP_SECRET).encode('utf-8'),
            str(self.request.user.email).encode('utf-8'),
            digestmod=hashlib.sha256).hexdigest()
        data = intercom(self.request)
        assert data['intercom_user_hash'] == expected_user_hash
        assert data['intercom_app_id'] == 'roger-roger'
        assert data['intercom_lms_url'] == self.request.site.domain

    def test_no_app_id(self):
        assert not hasattr(settings, 'INTERCOM_APP_ID')
        data = intercom(self.request)
        assert data['show_intercom_widget'] is False

        with override_settings(INTERCOM_APP_ID=None):
            data = intercom(self.request)
            assert data['show_intercom_widget'] is False

    @override_settings(INTERCOM_APP_ID='roger-roger')
    @patch(APPSEMBLER_APP + '.context_processors.should_show_intercom_widget',
           return_value=False)
    def test_app_id_unauthorized_user(self, _):
        data = intercom(self.request)
        assert data['show_intercom_widget'] is False
        assert 'intercom_user_hash' not in data
        assert 'intercom_app_id' not in data
