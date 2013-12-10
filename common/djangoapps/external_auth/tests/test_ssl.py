"""
Provides unit tests for SSL based authentication portions
of the external_auth app.
"""

import unittest

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory
from django.test.utils import override_settings

from external_auth.models import ExternalAuthMap
import external_auth.views

FEATURES_WITH_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITH_SSL_AUTH['AUTH_USE_MIT_CERTIFICATES'] = True
FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP = FEATURES_WITH_SSL_AUTH.copy()
FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP['AUTH_USE_MIT_CERTIFICATES_IMMEDIATE_SIGNUP'] = True


@override_settings(FEATURES=FEATURES_WITH_SSL_AUTH)
class SSLClientTest(TestCase):
    """
    Tests SSL Authentication code sections of external_auth
    """

    AUTH_DN = '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}'
    USER_NAME = 'test_user_ssl'
    USER_EMAIL = 'test_user_ssl@EDX.ORG'

    def _create_ssl_request(self, url):
        """Creates a basic request for SSL use."""
        request = self.factory.get(url)
        request.META['SSL_CLIENT_S_DN'] = self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        return request

    def setUp(self):
        """Setup test case by adding primary user."""
        super(SSLClientTest, self).setUp()
        self.client = Client()
        self.factory = RequestFactory()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_ssl_login_with_signup_lms(self):
        """
        Validate that an SSL login creates an eamap user and
        redirects them to the signup page.
        """

        response = external_auth.views.ssl_login(self._create_ssl_request('/'))

        # Response should contain template for signup form, eamap should have user, and internal
        # auth should not have a user
        self.assertIn('<form role="form" id="register-form" method="post"', response.content)
        try:
            ExternalAuthMap.objects.get(external_id=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to external auth map, exception was {0}'.format(str(ex)))

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email=self.USER_EMAIL)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
    @unittest.skip
    def test_ssl_login_with_signup_cms(self):
        """
        Validate that an SSL login creates an eamap user and
        redirects them to the signup page on CMS.

        This currently is failing and should be resolved to passing at
        some point.  using skip here instead of expectFailure because
        of an issue with nose.
        """
        self.client.get(
            reverse('contentstore.views.login_page'),
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        )

        try:
            ExternalAuthMap.objects.get(external_id=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to external auth map, exception was {0}'.format(str(ex)))

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email=self.USER_EMAIL)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_ssl_login_without_signup_lms(self):
        """
        Test IMMEDIATE_SIGNUP feature flag and ensure the user account is automatically created
        and the user is redirected to slash.
        """

        external_auth.views.ssl_login(self._create_ssl_request('/'))

        # Assert our user exists in both eamap and Users, and that we are logged in
        try:
            ExternalAuthMap.objects.get(external_id=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to external auth map, exception was {0}'.format(str(ex)))
        try:
            User.objects.get(email=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to internal users, exception was {0}'.format(str(ex)))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    @unittest.skip
    def test_ssl_login_without_signup_cms(self):
        """
        Test IMMEDIATE_SIGNUP feature flag and ensure the user account is
        automatically created on CMS.

        This currently is failing and should be resolved to passing at
        some point.  using skip here instead of expectFailure because
        of an issue with nose.
        """

        self.client.get(
            reverse('contentstore.views.login_page'),
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        )

        # Assert our user exists in both eamap and Users, and that we are logged in
        try:
            ExternalAuthMap.objects.get(external_id=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to external auth map, exception was {0}'.format(str(ex)))
        try:
            User.objects.get(email=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to internal users, exception was {0}'.format(str(ex)))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_default_login_decorator_ssl(self):
        """
        Make sure that SSL login happens if it is enabled on protected
        views instead of showing the login form.
        """
        response = self.client.get(reverse('dashboard'), follows=True)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts_login'), response['location'])

        response = self.client.get(
            reverse('dashboard'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL))
        self.assertIn(reverse('dashboard'), response['location'])
        self.assertIn('_auth_user_id', self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_registration_page_bypass(self):
        """
        This tests to make sure when immediate signup is on that
        the user doesn't get presented with the registration page.
        """
        response = self.client.get(
            reverse('register_user'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL))
        self.assertIn(reverse('dashboard'), response['location'])
        self.assertIn('_auth_user_id', self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_signin_page_bypass(self):
        """
        This tests to make sure when ssl authentication is on
        that user doesn't get presented with the login page if they
        have a certificate.
        """
        response = self.client.get(
            reverse('signin_user'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL))
        self.assertIn(reverse('dashboard'), response['location'])
        self.assertIn('_auth_user_id', self.client.session)
