""" Tests for views related to account settings and Tahoe IdP. """
# -*- coding: utf-8 -*-


from unittest import mock
from django.http import HttpRequest
from django.test import TestCase

from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangoapps.user_api.accounts.settings_views import account_settings_context
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.tests.factories import UserFactory
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin


@skip_unless_lms
class TahoeIdPAccountSettingsViewTest(ThirdPartyAuthTestMixin, SiteMixin, ProgramsApiConfigMixin, TestCase):
    """ Tests for the account settings view. """

    USERNAME = 'student'
    PASSWORD = 'password'
    FIELDS = [
        'country',
        'gender',
        'language',
        'level_of_education',
        'password',
        'year_of_birth',
        'preferred_language',
        'time_zone',
    ]

    @mock.patch("django.conf.settings.MESSAGE_STORAGE", 'django.contrib.messages.storage.cookie.CookieStorage')
    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

        self.request = HttpRequest()
        self.request.user = self.user

        # For these tests configure Tahoe IdP
        self.configure_google_provider(enabled=True, visible=True, name='Tahoe IdP')

        # Python-social saves auth failure notifcations in Django messages.
        # See pipeline.get_duplicate_provider() for details.
        self.request.COOKIES = {}

    @mock.patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    @mock.patch('openedx.core.djangoapps.appsembler.tahoe_idp.helpers.TAHOE_IDP_PROVIDER_NAME', 'oa2-google-oauth2')
    def test_context_with_tahoe_idp(self, mock_enterprise_customer_for_request):
        mock_enterprise_customer_for_request.return_value = {}

        default_context = account_settings_context(self.request)

        assert default_context['auth']['providers'], 'Should list providers'
        assert default_context['auth']['providers'][0]['name'] == 'Tahoe IdP'

        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_TAHOE_IDP': True}):
            context_tahoe_idp = account_settings_context(self.request)
            assert not context_tahoe_idp['auth']['providers'], 'Should remove the tahoe-idp provider'
