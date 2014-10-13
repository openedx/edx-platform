"""
Provides unit tests for SSL based authentication portions
of the external_auth app.
"""

import unittest

from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import Mock

import external_auth.views
from edxmako.middleware import MakoMiddleware
from external_auth.models import ExternalAuthMap
from opaque_keys import InvalidKeyError
from student.models import CourseEnrollment
from student.roles import CourseStaffRole
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import (ModuleStoreTestCase,
                                                    mixed_store_config)
from xmodule.modulestore.tests.factories import CourseFactory

FEATURES_WITH_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITH_SSL_AUTH['AUTH_USE_CERTIFICATES'] = True
FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP = FEATURES_WITH_SSL_AUTH.copy()
FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP['AUTH_USE_CERTIFICATES_IMMEDIATE_SIGNUP'] = True
FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE = FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP.copy()
FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH'] = True
FEATURES_WITHOUT_SSL_AUTH = settings.FEATURES.copy()
FEATURES_WITHOUT_SSL_AUTH['AUTH_USE_CERTIFICATES'] = False

TEST_DATA_MIXED_MODULESTORE = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {})

@override_settings(FEATURES=FEATURES_WITH_SSL_AUTH)
class SSLClientTest(ModuleStoreTestCase):
    """
    Tests SSL Authentication code sections of external_auth
    """

    AUTH_DN = '/C=US/ST=Massachusetts/O=Massachusetts Institute of Technology/OU=Client CA v1/CN={0}/emailAddress={1}'
    USER_NAME = 'test_user_ssl'
    USER_EMAIL = 'test_user_ssl@EDX.ORG'
    MOCK_URL = '/'

    def _create_ssl_request(self, url):
        """Creates a basic request for SSL use."""
        request = self.factory.get(url)
        request.META['SSL_CLIENT_S_DN'] = self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        MakoMiddleware().process_request(request)
        return request

    def _create_normal_request(self, url):
        """Creates sessioned request without SSL headers"""
        request = self.factory.get(url)
        request.user = AnonymousUser()
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        MakoMiddleware().process_request(request)
        return request

    def setUp(self):
        """Setup test case by adding primary user."""
        super(SSLClientTest, self).setUp()
        self.client = Client()
        self.factory = RequestFactory()
        self.mock = Mock()

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
    def test_ssl_login_with_signup_cms(self):
        """
        Validate that an SSL login creates an eamap user and
        redirects them to the signup page on CMS.
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
    def test_ssl_login_without_signup_cms(self):
        """
        Test IMMEDIATE_SIGNUP feature flag and ensure the user account is
        automatically created on CMS, and that we are redirected
        to courses.
        """

        response = self.client.get(
            reverse('contentstore.views.login_page'),
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/course', response['location'])

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
        self.assertEquals(('http://testserver/dashboard', 302),
                          response.redirect_chain[-1])
        self.assertIn(SESSION_KEY, self.client.session)

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
        self.assertEquals(('http://testserver/dashboard', 302),
                          response.redirect_chain[-1])
        self.assertIn(SESSION_KEY, self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_cms_registration_page_bypass(self):
        """
        This tests to make sure when immediate signup is on that
        the user doesn't get presented with the registration page.
        """
        response = self.client.get(
            reverse('signup'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        )
        self.assertEqual(response.status_code, 404)
        # assert that we are logged in
        self.assertIn(SESSION_KEY, self.client.session)

        # Now that we are logged in, make sure we don't see the registration page
        response = self.client.get(reverse('signup'), follow=True)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_signin_page_bypass(self):
        """
        This tests to make sure when ssl authentication is on
        that user doesn't get presented with the login page if they
        have a certificate.
        """
        # Test that they do signin if they don't have a cert
        response = self.client.get(reverse('signin_user'))
        self.assertEqual(200, response.status_code)
        self.assertTrue('login_form' in response.content
                        or 'login-form' in response.content)

        # And get directly logged in otherwise
        response = self.client.get(
            reverse('signin_user'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL))
        self.assertEquals(('http://testserver/dashboard', 302),
                          response.redirect_chain[-1])
        self.assertIn(SESSION_KEY, self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_ssl_bad_eamap(self):
        """
        This tests the response when a user exists but their eamap
        password doesn't match their internal password.

        The internal password use for certificates has been removed
        and this should not fail.
        """
        # Create account, break internal password, and activate account
        external_auth.views.ssl_login(self._create_ssl_request('/'))
        user = User.objects.get(email=self.USER_EMAIL)
        user.set_password('not autogenerated')
        user.is_active = True
        user.save()

        # Make sure we can still login
        self.client.get(
            reverse('signin_user'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL))
        self.assertIn(SESSION_KEY, self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITHOUT_SSL_AUTH)
    def test_ssl_decorator_no_certs(self):
        """Make sure no external auth happens without SSL enabled"""

        dec_mock = external_auth.views.ssl_login_shortcut(self.mock)
        request = self._create_normal_request(self.MOCK_URL)
        request.user = AnonymousUser()
        # Call decorated mock function to make sure it passes
        # the call through without hitting the external_auth functions and
        # thereby creating an external auth map object.
        dec_mock(request)
        self.assertTrue(self.mock.called)
        self.assertEqual(0, len(ExternalAuthMap.objects.all()))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_ssl_login_decorator(self):
        """Create mock function to test ssl login decorator"""

        dec_mock = external_auth.views.ssl_login_shortcut(self.mock)

        # Test that anonymous without cert doesn't create authmap
        request = self._create_normal_request(self.MOCK_URL)
        dec_mock(request)
        self.assertTrue(self.mock.called)
        self.assertEqual(0, len(ExternalAuthMap.objects.all()))

        # Test valid user
        self.mock.reset_mock()
        request = self._create_ssl_request(self.MOCK_URL)
        dec_mock(request)
        self.assertFalse(self.mock.called)
        self.assertEqual(1, len(ExternalAuthMap.objects.all()))

        # Test logged in user gets called
        self.mock.reset_mock()
        request = self._create_ssl_request(self.MOCK_URL)
        request.user = UserFactory()
        dec_mock(request)
        self.assertTrue(self.mock.called)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_IMMEDIATE_SIGNUP)
    def test_ssl_decorator_auto_signup(self):
        """
        Test that with auto signup the decorator
        will bypass registration and call retfun.
        """

        dec_mock = external_auth.views.ssl_login_shortcut(self.mock)
        request = self._create_ssl_request(self.MOCK_URL)
        dec_mock(request)
        # Assert our user exists in both eamap and Users
        try:
            ExternalAuthMap.objects.get(external_id=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to external auth map, exception was {0}'.format(str(ex)))
        try:
            User.objects.get(email=self.USER_EMAIL)
        except ExternalAuthMap.DoesNotExist, ex:
            self.fail('User did not get properly added to internal users, exception was {0}'.format(str(ex)))
        self.assertEqual(1, len(ExternalAuthMap.objects.all()))

        self.assertTrue(self.mock.called)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE,
                       MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
    def test_ssl_lms_redirection(self):
        """
        Auto signup auth user and ensure they return to the original
        url they visited after being logged in.
        """
        course = CourseFactory.create(
            org='MITx',
            number='999',
            display_name='Robot Super Course'
        )

        external_auth.views.ssl_login(self._create_ssl_request('/'))
        user = User.objects.get(email=self.USER_EMAIL)
        CourseEnrollment.enroll(user, course.id)
        course_private_url = '/courses/MITx/999/Robot_Super_Course/courseware'

        self.assertFalse(SESSION_KEY in self.client.session)

        response = self.client.get(
            course_private_url,
            follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL),
            HTTP_ACCEPT='text/html'
        )
        self.assertEqual(('http://testserver{0}'.format(course_private_url), 302),
                         response.redirect_chain[-1])
        self.assertIn(SESSION_KEY, self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in cms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE)
    def test_ssl_cms_redirection(self):
        """
        Auto signup auth user and ensure they return to the original
        url they visited after being logged in.
        """
        course = CourseFactory.create(
            org='MITx',
            number='999',
            display_name='Robot Super Course'
        )

        external_auth.views.ssl_login(self._create_ssl_request('/'))
        user = User.objects.get(email=self.USER_EMAIL)
        CourseEnrollment.enroll(user, course.id)

        CourseStaffRole(course.id).add_users(user)
        course_private_url = reverse('course_handler', args=(unicode(course.id),))
        self.assertFalse(SESSION_KEY in self.client.session)

        response = self.client.get(
            course_private_url,
            follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL),
            HTTP_ACCEPT='text/html'
        )
        self.assertEqual(('http://testserver{0}'.format(course_private_url), 302),
                         response.redirect_chain[-1])
        self.assertIn(SESSION_KEY, self.client.session)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @override_settings(FEATURES=FEATURES_WITH_SSL_AUTH_AUTO_ACTIVATE)
    def test_ssl_logout(self):
        """
        Because the branding view is cached for anonymous users and we
        use that to login users, the browser wasn't actually making the
        request to that view as the redirect was being cached. This caused
        a redirect loop, and this test confirms that that won't happen.

        Test is only in LMS because we don't use / in studio to login SSL users.
        """
        response = self.client.get(
            reverse('dashboard'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL))
        self.assertEquals(('http://testserver/dashboard', 302),
                          response.redirect_chain[-1])
        self.assertIn(SESSION_KEY, self.client.session)
        response = self.client.get(
            reverse('logout'), follow=True,
            SSL_CLIENT_S_DN=self.AUTH_DN.format(self.USER_NAME, self.USER_EMAIL)
        )
        # Make sure that even though we logged out, we have logged back in
        self.assertIn(SESSION_KEY, self.client.session)
