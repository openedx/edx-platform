"Tests for account creation"

import ddt
import unittest
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser
from django.utils.importlib import import_module
from django.test import TestCase, TransactionTestCase

import mock

from user_api.models import UserPreference
from lang_pref import LANGUAGE_KEY

from edxmako.tests import mako_middleware_process_request
from external_auth.models import ExternalAuthMap
import student

TEST_CS_URL = 'https://comments.service.test:123/'


@ddt.ddt
class TestCreateAccount(TestCase):
    "Tests for account creation"

    def setUp(self):
        self.username = "test_user"
        self.url = reverse("create_account")
        self.request_factory = RequestFactory()
        self.params = {
            "username": self.username,
            "email": "test@example.org",
            "password": "testpass",
            "name": "Test User",
            "honor_code": "true",
            "terms_of_service": "true",
        }

    @ddt.data("en", "eo")
    def test_default_lang_pref_saved(self, lang):
        with mock.patch("django.conf.settings.LANGUAGE_CODE", lang):
            response = self.client.post(self.url, self.params)
            self.assertEqual(response.status_code, 200)
            user = User.objects.get(username=self.username)
            self.assertEqual(UserPreference.get_preference(user, LANGUAGE_KEY), lang)

    @ddt.data("en", "eo")
    def test_header_lang_pref_saved(self, lang):
        response = self.client.post(self.url, self.params, HTTP_ACCEPT_LANGUAGE=lang)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=self.username)
        self.assertEqual(UserPreference.get_preference(user, LANGUAGE_KEY), lang)

    def base_extauth_bypass_sending_activation_email(self, bypass_activation_email_for_extauth_setting):
        """
        Tests user creation without sending activation email when
        doing external auth
        """

        request = self.request_factory.post(self.url, self.params)
        # now indicate we are doing ext_auth by setting 'ExternalAuthMap' in the session.
        request.session = import_module(settings.SESSION_ENGINE).SessionStore()  # empty session
        extauth = ExternalAuthMap(external_id='withmap@stanford.edu',
                                  external_email='withmap@stanford.edu',
                                  internal_password=self.params['password'],
                                  external_domain='shib:https://idp.stanford.edu/')
        request.session['ExternalAuthMap'] = extauth
        request.user = AnonymousUser()

        mako_middleware_process_request(request)
        with mock.patch('django.contrib.auth.models.User.email_user') as mock_send_mail:
            student.views.create_account(request)

        # check that send_mail is called
        if bypass_activation_email_for_extauth_setting:
            self.assertFalse(mock_send_mail.called)
        else:
            self.assertTrue(mock_send_mail.called)

    @unittest.skipUnless(settings.FEATURES.get('AUTH_USE_SHIB'), "AUTH_USE_SHIB not set")
    @mock.patch.dict(settings.FEATURES, {'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': True, 'AUTOMATIC_AUTH_FOR_TESTING': False})
    def test_extauth_bypass_sending_activation_email_with_bypass(self):
        """
        Tests user creation without sending activation email when
        settings.FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH']=True and doing external auth
        """
        self.base_extauth_bypass_sending_activation_email(True)

    @unittest.skipUnless(settings.FEATURES.get('AUTH_USE_SHIB'), "AUTH_USE_SHIB not set")
    @mock.patch.dict(settings.FEATURES, {'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False, 'AUTOMATIC_AUTH_FOR_TESTING': False})
    def test_extauth_bypass_sending_activation_email_without_bypass(self):
        """
        Tests user creation without sending activation email when
        settings.FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH']=False and doing external auth
        """
        self.base_extauth_bypass_sending_activation_email(False)


@mock.patch.dict("student.models.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
@mock.patch("lms.lib.comment_client.User.base_url", TEST_CS_URL)
@mock.patch("lms.lib.comment_client.utils.requests.request", return_value=mock.Mock(status_code=200, text='{}'))
class TestCreateCommentsServiceUser(TransactionTestCase):

    def setUp(self):
        self.username = "test_user"
        self.url = reverse("create_account")
        self.params = {
            "username": self.username,
            "email": "test@example.org",
            "password": "testpass",
            "name": "Test User",
            "honor_code": "true",
            "terms_of_service": "true",
        }

    def test_cs_user_created(self, request):
        "If user account creation succeeds, we should create a comments service user"
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(request.called)
        args, kwargs = request.call_args
        self.assertEqual(args[0], 'put')
        self.assertTrue(args[1].startswith(TEST_CS_URL))
        self.assertEqual(kwargs['data']['username'], self.params['username'])

    @mock.patch("student.models.Registration.register", side_effect=Exception)
    def test_cs_user_not_created(self, register, request):
        "If user account creation fails, we should not create a comments service user"
        try:
            response = self.client.post(self.url, self.params)
        except:
            pass
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username=self.username)
        self.assertTrue(register.called)
        self.assertFalse(request.called)
