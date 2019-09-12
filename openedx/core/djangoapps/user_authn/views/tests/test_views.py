# -*- coding: utf-8 -*-
""" Tests for user authn views. """

from http.cookies import SimpleCookie
import logging
import re
from unittest import skipUnless
from urllib import urlencode

import ddt
import mock
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.urls import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.utils.translation import ugettext as _
from edx_oauth2_provider.tests.factories import AccessTokenFactory, ClientFactory, RefreshTokenFactory
from oauth2_provider.models import AccessToken as dot_access_token
from oauth2_provider.models import RefreshToken as dot_refresh_token
from provider.oauth2.models import AccessToken as dop_access_token
from provider.oauth2.models import RefreshToken as dop_refresh_token
from testfixtures import LogCapture
from waffle.models import Switch
from waffle.testutils import override_switch

from course_modes.models import CourseMode
from openedx.core.djangoapps.user_authn.views.login_form import login_and_registration_form
from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme_context
from openedx.core.djangoapps.user_api.accounts.api import activate_account, create_account
from openedx.core.djangoapps.user_api.errors import UserAPIInternalError
from openedx.core.djangoapps.user_api.accounts.utils import ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH
from openedx.core.djangolib.js_utils import dump_js_escaped_json
from openedx.core.djangolib.markup import HTML, Text
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from student.tests.factories import AccountRecoveryFactory
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin, simulate_running_pipeline
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

LOGGER_NAME = 'audit'
User = get_user_model()  # pylint:disable=invalid-name

FEATURES_WITH_FAILED_PASSWORD_RESET_EMAIL = settings.FEATURES.copy()
FEATURES_WITH_FAILED_PASSWORD_RESET_EMAIL['ENABLE_PASSWORD_RESET_FAILURE_EMAIL'] = True


@skip_unless_lms
@ddt.ddt
class UserAccountUpdateTest(CacheIsolationTestCase, UrlResetMixin):
    """ Tests for views that update the user's account information. """

    USERNAME = u"heisenberg"
    ALTERNATE_USERNAME = u"walt"
    OLD_PASSWORD = u"ḅḷüëṡḳÿ"
    NEW_PASSWORD = u"B🄸🄶B🄻🅄🄴"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

    INVALID_KEY = u"123abc"

    URLCONF_MODULES = ['student_accounts.urls']

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(UserAccountUpdateTest, self).setUp()

        # Create/activate a new account
        activation_key = create_account(self.USERNAME, self.OLD_PASSWORD, self.OLD_EMAIL)
        activate_account(activation_key)

        self.account_recovery = AccountRecoveryFactory.create(user=User.objects.get(email=self.OLD_EMAIL))
        self.enable_account_recovery_switch = Switch.objects.create(
            name=ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH,
            active=True
        )

        # Login
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertTrue(result)

    @skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_password_change(self):
        # Request a password change while logged in, simulating
        # use of the password reset link from the account page
        response = self._change_password()
        self.assertEqual(response.status_code, 200)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Retrieve the activation link from the email body
        email_body = mail.outbox[0].body
        result = re.search(r'(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)
        activation_link = result.group('url')

        # Visit the activation link
        response = self.client.get(activation_link)
        self.assertEqual(response.status_code, 200)

        # Submit a new password and follow the redirect to the success page
        response = self.client.post(
            activation_link,
            # These keys are from the form on the current password reset confirmation page.
            {'new_password1': self.NEW_PASSWORD, 'new_password2': self.NEW_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your password has been reset.")

        # Log the user out to clear session data
        self.client.logout()

        # Verify that the new password can be used to log in
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)

        # Try reusing the activation link to change the password again
        # Visit the activation link again.
        response = self.client.get(activation_link)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password reset link is invalid. It may have been used already.")

        self.client.logout()

        # Verify that the old password cannot be used to log in
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertFalse(result)

        # Verify that the new password continues to be valid
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)

    def test_password_change_failure(self):
        with mock.patch('openedx.core.djangoapps.user_api.accounts.api.request_password_change',
                        side_effect=UserAPIInternalError):
            self._change_password()
            self.assertRaises(UserAPIInternalError)

    @override_settings(FEATURES=FEATURES_WITH_FAILED_PASSWORD_RESET_EMAIL)
    def test_password_reset_failure_email(self):
        """Test that a password reset failure email notification is sent, when enabled."""
        # Log the user out
        self.client.logout()

        bad_email = 'doesnotexist@example.com'
        response = self._change_password(email=bad_email)
        self.assertEqual(response.status_code, 200)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the body contains the failed password reset message
        sent_message = mail.outbox[0]
        text_body = sent_message.body
        html_body = sent_message.alternatives[0][0]

        for email_body in [text_body, html_body]:
            msg = 'However, there is currently no user account associated with your email address: {email}'.format(
                email=bad_email
            )

            assert u'reset for your user account at {}'.format(settings.PLATFORM_NAME) in email_body
            assert 'password_reset_confirm' not in email_body, 'The link should not be added if user was not found'
            assert msg in email_body

    @ddt.data(True, False)
    def test_password_change_logged_out(self, send_email):
        # Log the user out
        self.client.logout()

        # Request a password change while logged out, simulating
        # use of the password reset link from the login page
        if send_email:
            response = self._change_password(email=self.OLD_EMAIL)
            self.assertEqual(response.status_code, 200)
        else:
            # Don't send an email in the POST data, simulating
            # its (potentially accidental) omission in the POST
            # data sent from the login page
            response = self._change_password()
            self.assertEqual(response.status_code, 400)

    def test_access_token_invalidation_logged_out(self):
        self.client.logout()
        user = User.objects.get(email=self.OLD_EMAIL)
        self._create_dop_tokens(user)
        self._create_dot_tokens(user)
        response = self._change_password(email=self.OLD_EMAIL)
        self.assertEqual(response.status_code, 200)
        self.assert_access_token_destroyed(user)

    def test_access_token_invalidation_logged_in(self):
        user = User.objects.get(email=self.OLD_EMAIL)
        self._create_dop_tokens(user)
        self._create_dot_tokens(user)
        response = self._change_password()
        self.assertEqual(response.status_code, 200)
        self.assert_access_token_destroyed(user)

    def test_password_change_inactive_user(self):
        # Log out the user created during test setup
        self.client.logout()

        # Create a second user, but do not activate it
        create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)

        # Send the view the email address tied to the inactive user
        response = self._change_password(email=self.NEW_EMAIL)

        # Expect that the activation email is still sent,
        # since the user may have lost the original activation email.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_change_no_user(self):
        # Log out the user created during test setup
        self.client.logout()

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            # Send the view an email address not tied to any user
            response = self._change_password(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, 200)
            logger.check((LOGGER_NAME, 'INFO', 'Invalid password reset attempt'))

    def test_password_change_rate_limited(self):
        """
        Tests that consective password reset requests are rate limited.
        """
        # Log out the user created during test setup, to prevent the view from
        # selecting the logged-in user's email address over the email provided
        # in the POST data
        self.client.logout()

        for status in [200, 403]:
            response = self._change_password(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, status)

        with mock.patch(
            'util.request_rate_limiter.PasswordResetEmailRateLimiter.is_rate_limit_exceeded',
            return_value=False
        ):
            response = self._change_password(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, 200)

    @ddt.data(
        ('post', 'password_change_request', []),
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name, args):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name, args=args)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    @override_switch(ENABLE_SECONDARY_EMAIL_FEATURE_SWITCH, active=False)
    def test_404_if_account_recovery_not_enabled(self):
        with mock.patch('openedx.core.djangoapps.user_api.accounts.api.request_account_recovery',
                        side_effect=UserAPIInternalError):
            self._recover_account()
            self.assertRaises(Http404)

    def test_account_recovery_failure(self):
        with mock.patch('openedx.core.djangoapps.user_api.accounts.api.request_account_recovery',
                        side_effect=UserAPIInternalError):
            self._recover_account()
            self.assertRaises(UserAPIInternalError)

    @override_settings(FEATURES=FEATURES_WITH_FAILED_PASSWORD_RESET_EMAIL)
    def test_account_recovery_failure_email(self):
        """Test that log message is added when email does not match any in the system."""
        # Log the user out
        self.client.logout()

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            bad_email = 'doesnotexist@example.com'
            response = self._recover_account(email=bad_email)
            self.assertEqual(response.status_code, 200)
            logger.check(
                (
                    LOGGER_NAME,
                    "WARNING", "Account recovery attempt via invalid secondary email '{email}'.".format(
                        email=bad_email
                    )
                )
            )

    @override_settings(FEATURES=FEATURES_WITH_FAILED_PASSWORD_RESET_EMAIL)
    def test_account_recovery_failure_not_active(self):
        """Test that log message is added when email does not match any active account recovery records."""
        # Log the user out
        self.client.logout()
        self.account_recovery.is_active = False
        self.account_recovery.save()

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            response = self._recover_account(email=self.account_recovery.secondary_email)
            self.assertEqual(response.status_code, 200)
            logger.check(
                (
                    LOGGER_NAME,
                    "WARNING", "Account recovery attempt via invalid secondary email '{email}'.".format(
                        email=self.account_recovery.secondary_email
                    )
                )
            )

    def test_password_change_rate_limited_during_account_recovery(self):
        """
        Tests that consective password reset requests during account recovery are rate limited.
        """
        # Log out the user created during test setup, to prevent the view from
        # selecting the logged-in user's email address over the email provided
        # in the POST data
        self.client.logout()

        for status in [200, 403]:
            response = self._recover_account(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, status)

        with mock.patch(
            'util.request_rate_limiter.PasswordResetEmailRateLimiter.is_rate_limit_exceeded',
            return_value=False
        ):
            response = self._recover_account(email=self.NEW_EMAIL)
            self.assertEqual(response.status_code, 200)

    @ddt.data(
        ('post', 'account_recovery', []),
    )
    @ddt.unpack
    def test_require_http_method_during_account_recovery(self, correct_method, url_name, args):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name, args=args)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    def _change_password(self, email=None):
        """Request to change the user's password. """
        data = {}

        if email:
            data['email'] = email

        return self.client.post(path=reverse('password_change_request'), data=data)

    def _recover_account(self, email=None):
        """Request to create the user's password. """
        data = {}

        if email:
            data['email'] = email

        return self.client.post(path=reverse('account_recovery'), data=data)

    def _create_dop_tokens(self, user=None):
        """Create dop access token for given user if user provided else for default user."""
        if not user:
            user = User.objects.get(email=self.OLD_EMAIL)

        client = ClientFactory()
        access_token = AccessTokenFactory(user=user, client=client)
        RefreshTokenFactory(user=user, client=client, access_token=access_token)

    def _create_dot_tokens(self, user=None):
        """Create dop access token for given user if user provided else for default user."""
        if not user:
            user = User.objects.get(email=self.OLD_EMAIL)

        application = dot_factories.ApplicationFactory(user=user)
        access_token = dot_factories.AccessTokenFactory(user=user, application=application)
        dot_factories.RefreshTokenFactory(user=user, application=application, access_token=access_token)

    def assert_access_token_destroyed(self, user):
        """Assert all access tokens are destroyed."""
        self.assertFalse(dot_access_token.objects.filter(user=user).exists())
        self.assertFalse(dot_refresh_token.objects.filter(user=user).exists())
        self.assertFalse(dop_access_token.objects.filter(user=user).exists())
        self.assertFalse(dop_refresh_token.objects.filter(user=user).exists())


@skip_unless_lms
@ddt.ddt
class LoginAndRegistrationTest(ThirdPartyAuthTestMixin, UrlResetMixin, ModuleStoreTestCase):
    """ Tests for the student account views that update the user's account information. """
    shard = 7
    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = u"password"

    URLCONF_MODULES = ['openedx.core.djangoapps.embargo']

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):  # pylint: disable=arguments-differ
        super(LoginAndRegistrationTest, self).setUp()

        # Several third party auth providers are created for these tests:
        self.google_provider = self.configure_google_provider(enabled=True, visible=True)
        self.configure_facebook_provider(enabled=True, visible=True)
        self.configure_dummy_provider(
            visible=True,
            enabled=True,
            icon_class='',
            icon_image=SimpleUploadedFile('icon.svg', '<svg><rect width="50" height="100"/></svg>'),
        )
        self.hidden_enabled_provider = self.configure_linkedin_provider(
            visible=False,
            enabled=True,
        )
        self.hidden_disabled_provider = self.configure_azure_ad_provider()

    @ddt.data(
        ("signin_user", "login"),
        ("register_user", "register"),
    )
    @ddt.unpack
    def test_login_and_registration_form(self, url_name, initial_mode):
        response = self.client.get(reverse(url_name))
        expected_data = '"initial_mode": "{mode}"'.format(mode=initial_mode)
        self.assertContains(response, expected_data)

    @ddt.data("signin_user", "register_user")
    def test_login_and_registration_form_already_authenticated(self, url_name):
        # call the account registration api that sets the login cookies
        url = reverse('user_api_registration')
        request_data = {
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'email': self.EMAIL,
            'name': self.USERNAME,
            'terms_of_service': 'true',
            'honor_code': 'true',
        }
        result = self.client.post(url, data=request_data)
        self.assertEqual(result.status_code, 200)

        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

        # Verify that we're redirected to the dashboard
        response = self.client.get(reverse(url_name))
        self.assertRedirects(response, reverse("dashboard"))

    @ddt.data(
        (None, "signin_user"),
        (None, "register_user"),
        ("edx.org", "signin_user"),
        ("edx.org", "register_user"),
    )
    @ddt.unpack
    def test_login_and_registration_form_signin_not_preserves_params(self, theme, url_name):
        params = [
            ('course_id', 'edX/DemoX/Demo_Course'),
            ('enrollment_action', 'enroll'),
        ]

        # The response should not have a "Sign In" button with the URL
        # that preserves the querystring params
        with with_comprehensive_theme_context(theme):
            response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")

        expected_url = '/login?{}'.format(self._finish_auth_url_param(params + [('next', '/dashboard')]))
        self.assertNotContains(response, expected_url)

        # Add additional parameters:
        params = [
            ('course_id', 'edX/DemoX/Demo_Course'),
            ('enrollment_action', 'enroll'),
            ('course_mode', CourseMode.DEFAULT_MODE_SLUG),
            ('email_opt_in', 'true'),
            ('next', '/custom/final/destination')
        ]

        # Verify that this parameter is also preserved
        with with_comprehensive_theme_context(theme):
            response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")

        expected_url = '/login?{}'.format(self._finish_auth_url_param(params))
        self.assertNotContains(response, expected_url)

    @mock.patch.dict(settings.FEATURES, {"ENABLE_THIRD_PARTY_AUTH": False})
    @ddt.data("signin_user", "register_user")
    def test_third_party_auth_disabled(self, url_name):
        response = self.client.get(reverse(url_name))
        self._assert_third_party_auth_data(response, None, None, [], None)

    @mock.patch('openedx.core.djangoapps.user_authn.views.login_form.enterprise_customer_for_request')
    @mock.patch('openedx.core.djangoapps.user_api.api.enterprise_customer_for_request')
    @ddt.data(
        ("signin_user", None, None, None, False),
        ("register_user", None, None, None, False),
        ("signin_user", "google-oauth2", "Google", None, False),
        ("register_user", "google-oauth2", "Google", None, False),
        ("signin_user", "facebook", "Facebook", None, False),
        ("register_user", "facebook", "Facebook", None, False),
        ("signin_user", "dummy", "Dummy", None, False),
        ("register_user", "dummy", "Dummy", None, False),
        (
            "signin_user",
            "google-oauth2",
            "Google",
            {
                'name': 'FakeName',
                'logo': 'https://host.com/logo.jpg',
                'welcome_msg': 'No message'
            },
            True
        )
    )
    @ddt.unpack
    def test_third_party_auth(
            self,
            url_name,
            current_backend,
            current_provider,
            expected_enterprise_customer_mock_attrs,
            add_user_details,
            enterprise_customer_mock_1,
            enterprise_customer_mock_2
    ):
        params = [
            ('course_id', 'course-v1:Org+Course+Run'),
            ('enrollment_action', 'enroll'),
            ('course_mode', CourseMode.DEFAULT_MODE_SLUG),
            ('email_opt_in', 'true'),
            ('next', '/custom/final/destination'),
        ]

        if expected_enterprise_customer_mock_attrs:
            expected_ec = {
                'name': expected_enterprise_customer_mock_attrs['name'],
                'branding_configuration': {
                    'logo': 'https://host.com/logo.jpg',
                    'welcome_message': expected_enterprise_customer_mock_attrs['welcome_msg']
                }
            }
        else:
            expected_ec = None

        email = None
        if add_user_details:
            email = 'test@test.com'
        enterprise_customer_mock_1.return_value = expected_ec
        enterprise_customer_mock_2.return_value = expected_ec

        # Simulate a running pipeline
        if current_backend is not None:
            pipeline_target = "openedx.core.djangoapps.user_authn.views.login_form.third_party_auth.pipeline"
            with simulate_running_pipeline(pipeline_target, current_backend, email=email):
                response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")

        # Do NOT simulate a running pipeline
        else:
            response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")

        # This relies on the THIRD_PARTY_AUTH configuration in the test settings
        expected_providers = [
            {
                "id": "oa2-dummy",
                "name": "Dummy",
                "iconClass": None,
                "iconImage": settings.MEDIA_URL + "icon.svg",
                "loginUrl": self._third_party_login_url("dummy", "login", params),
                "registerUrl": self._third_party_login_url("dummy", "register", params)
            },
            {
                "id": "oa2-facebook",
                "name": "Facebook",
                "iconClass": "fa-facebook",
                "iconImage": None,
                "loginUrl": self._third_party_login_url("facebook", "login", params),
                "registerUrl": self._third_party_login_url("facebook", "register", params)
            },
            {
                "id": "oa2-google-oauth2",
                "name": "Google",
                "iconClass": "fa-google-plus",
                "iconImage": None,
                "loginUrl": self._third_party_login_url("google-oauth2", "login", params),
                "registerUrl": self._third_party_login_url("google-oauth2", "register", params)
            },
        ]
        self._assert_third_party_auth_data(
            response,
            current_backend,
            current_provider,
            expected_providers,
            expected_ec,
            add_user_details
        )

    def _configure_testshib_provider(self, provider_name, idp_slug):
        """
        Enable and configure the TestShib SAML IdP as a third_party_auth provider.
        """
        kwargs = {}
        kwargs.setdefault('name', provider_name)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('visible', True)
        kwargs.setdefault('slug', idp_slug)
        kwargs.setdefault('entity_id', 'https://idp.testshib.org/idp/shibboleth')
        kwargs.setdefault('metadata_source', 'https://mock.testshib.org/metadata/testshib-providers.xml')
        kwargs.setdefault('icon_class', 'fa-university')
        kwargs.setdefault('attr_email', 'dummy-email-attr')
        kwargs.setdefault('max_session_length', None)
        self.configure_saml_provider(**kwargs)

    @mock.patch('django.conf.settings.MESSAGE_STORAGE', 'django.contrib.messages.storage.cookie.CookieStorage')
    @mock.patch('openedx.core.djangoapps.user_authn.views.login_form.enterprise_customer_for_request')
    @ddt.data(
        (
            'signin_user',
            'tpa-saml',
            'TestShib',
        )
    )
    @ddt.unpack
    def test_saml_auth_with_error(
            self,
            url_name,
            current_backend,
            current_provider,
            enterprise_customer_mock,
    ):
        params = []
        request = RequestFactory().get(reverse(url_name), params, HTTP_ACCEPT='text/html')
        SessionMiddleware().process_request(request)
        request.user = AnonymousUser()

        self.enable_saml()
        dummy_idp = 'testshib'
        self._configure_testshib_provider(current_provider, dummy_idp)
        enterprise_customer_data = {
            'uuid': '72416e52-8c77-4860-9584-15e5b06220fb',
            'name': 'Dummy Enterprise',
            'identity_provider': dummy_idp,
        }
        enterprise_customer_mock.return_value = enterprise_customer_data
        dummy_error_message = 'Authentication failed: SAML login failed ' \
                              '["invalid_response"] [SAML Response must contain 1 assertion]'

        # Add error message for error in auth pipeline
        MessageMiddleware().process_request(request)
        messages.error(request, dummy_error_message, extra_tags='social-auth')

        # Simulate a running pipeline
        pipeline_response = {
            'response': {
                'idp_name': dummy_idp
            }
        }
        pipeline_target = 'openedx.core.djangoapps.user_authn.views.login_form.third_party_auth.pipeline'
        with simulate_running_pipeline(pipeline_target, current_backend, **pipeline_response):
            with mock.patch('edxmako.request_context.get_current_request', return_value=request):
                response = login_and_registration_form(request)

        expected_error_message = Text(_(
            u'We are sorry, you are not authorized to access {platform_name} via this channel. '
            u'Please contact your learning administrator or manager in order to access {platform_name}.'
            u'{line_break}{line_break}'
            u'Error Details:{line_break}{error_message}')
        ).format(
            platform_name=settings.PLATFORM_NAME,
            error_message=dummy_error_message,
            line_break=HTML('<br/>')
        )
        self._assert_saml_auth_data_with_error(
            response,
            current_backend,
            current_provider,
            expected_error_message
        )

    def test_hinted_login(self):
        params = [("next", "/courses/something/?tpa_hint=oa2-google-oauth2")]
        response = self.client.get(reverse('signin_user'), params, HTTP_ACCEPT="text/html")
        self.assertContains(response, '"third_party_auth_hint": "oa2-google-oauth2"')

        tpa_hint = self.hidden_enabled_provider.provider_id
        params = [("next", "/courses/something/?tpa_hint={0}".format(tpa_hint))]
        response = self.client.get(reverse('signin_user'), params, HTTP_ACCEPT="text/html")
        self.assertContains(response, '"third_party_auth_hint": "{0}"'.format(tpa_hint))

        tpa_hint = self.hidden_disabled_provider.provider_id
        params = [("next", "/courses/something/?tpa_hint={0}".format(tpa_hint))]
        response = self.client.get(reverse('signin_user'), params, HTTP_ACCEPT="text/html")
        self.assertNotIn(response.content, tpa_hint)

    @ddt.data(
        ('signin_user', 'login'),
        ('register_user', 'register'),
    )
    @ddt.unpack
    def test_hinted_login_dialog_disabled(self, url_name, auth_entry):
        """Test that the dialog doesn't show up for hinted logins when disabled. """
        self.google_provider.skip_hinted_login_dialog = True
        self.google_provider.save()
        params = [("next", "/courses/something/?tpa_hint=oa2-google-oauth2")]
        response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")
        expected_url = '/auth/login/google-oauth2/?auth_entry={}&next=%2Fcourses'\
                       '%2Fsomething%2F%3Ftpa_hint%3Doa2-google-oauth2'.format(auth_entry)
        self.assertRedirects(
            response,
            expected_url,
            target_status_code=302
        )

    @override_settings(FEATURES=dict(settings.FEATURES, THIRD_PARTY_AUTH_HINT='oa2-google-oauth2'))
    @ddt.data(
        'signin_user',
        'register_user',
    )
    def test_settings_tpa_hinted_login(self, url_name):
        """
        Ensure that settings.FEATURES['THIRD_PARTY_AUTH_HINT'] can set third_party_auth_hint.
        """
        params = [("next", "/courses/something/")]
        response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")
        self.assertContains(response, '"third_party_auth_hint": "oa2-google-oauth2"')

        # THIRD_PARTY_AUTH_HINT can be overridden via the query string
        tpa_hint = self.hidden_enabled_provider.provider_id
        params = [("next", "/courses/something/?tpa_hint={0}".format(tpa_hint))]
        response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")
        self.assertContains(response, '"third_party_auth_hint": "{0}"'.format(tpa_hint))

        # Even disabled providers in the query string will override THIRD_PARTY_AUTH_HINT
        tpa_hint = self.hidden_disabled_provider.provider_id
        params = [("next", "/courses/something/?tpa_hint={0}".format(tpa_hint))]
        response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")
        self.assertNotIn(response.content, tpa_hint)

    @override_settings(FEATURES=dict(settings.FEATURES, THIRD_PARTY_AUTH_HINT='oa2-google-oauth2'))
    @ddt.data(
        ('signin_user', 'login'),
        ('register_user', 'register'),
    )
    @ddt.unpack
    def test_settings_tpa_hinted_login_dialog_disabled(self, url_name, auth_entry):
        """Test that the dialog doesn't show up for hinted logins when disabled via settings.THIRD_PARTY_AUTH_HINT. """
        self.google_provider.skip_hinted_login_dialog = True
        self.google_provider.save()
        params = [("next", "/courses/something/")]
        response = self.client.get(reverse(url_name), params, HTTP_ACCEPT="text/html")
        expected_url = '/auth/login/google-oauth2/?auth_entry={}&next=%2Fcourses'\
                       '%2Fsomething%2F%3Ftpa_hint%3Doa2-google-oauth2'.format(auth_entry)
        self.assertRedirects(
            response,
            expected_url,
            target_status_code=302
        )

    @mock.patch('openedx.core.djangoapps.user_authn.views.login_form.enterprise_customer_for_request')
    @ddt.data(
        ('signin_user', False, None, None),
        ('register_user', False, None, None),
        ('signin_user', True, 'Fake EC', 'http://logo.com/logo.jpg'),
        ('register_user', True, 'Fake EC', 'http://logo.com/logo.jpg'),
        ('signin_user', True, 'Fake EC', None),
        ('register_user', True, 'Fake EC', None),
    )
    @ddt.unpack
    def test_enterprise_register(self, url_name, ec_present, ec_name, logo_url, mock_get_ec):
        """
        Verify that when an EnterpriseCustomer is received on the login and register views,
        the appropriate sidebar is rendered.
        """
        if ec_present:
            mock_get_ec.return_value = {
                'name': ec_name,
                'branding_configuration': {'logo': logo_url}
            }
        else:
            mock_get_ec.return_value = None

        response = self.client.get(reverse(url_name), HTTP_ACCEPT="text/html")

        enterprise_sidebar_div_id = u'enterprise-content-container'

        if not ec_present:
            self.assertNotContains(response, text=enterprise_sidebar_div_id)
        else:
            self.assertContains(response, text=enterprise_sidebar_div_id)
            welcome_message = settings.ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE
            expected_message = Text(welcome_message).format(
                start_bold=HTML('<b>'),
                end_bold=HTML('</b>'),
                line_break=HTML('<br/>'),
                enterprise_name=ec_name,
                platform_name=settings.PLATFORM_NAME,
                privacy_policy_link_start=HTML("<a href='{pp_url}' rel='noopener' target='_blank'>").format(
                    pp_url=settings.MKTG_URLS.get('PRIVACY', 'https://www.edx.org/edx-privacy-policy')
                ),
                privacy_policy_link_end=HTML("</a>"),
            )
            self.assertContains(response, expected_message)
            if logo_url:
                self.assertContains(response, logo_url)

    def test_enterprise_cookie_delete(self):
        """
        Test that enterprise cookies are deleted in login/registration views.

        Cookies must be deleted in login/registration views so that *default* login/registration branding
        is displayed to subsequent requests from non-enterprise customers.
        """
        cookies = SimpleCookie()
        cookies[settings.ENTERPRISE_CUSTOMER_COOKIE_NAME] = 'test-enterprise-customer'
        response = self.client.get(reverse('signin_user'), HTTP_ACCEPT="text/html", cookies=cookies)

        self.assertIn(settings.ENTERPRISE_CUSTOMER_COOKIE_NAME, response.cookies)
        enterprise_cookie = response.cookies[settings.ENTERPRISE_CUSTOMER_COOKIE_NAME]

        self.assertEqual(enterprise_cookie['domain'], settings.BASE_COOKIE_DOMAIN)
        self.assertEqual(enterprise_cookie.value, '')

    def test_login_registration_xframe_protected(self):
        resp = self.client.get(
            reverse("register_user"),
            {},
            HTTP_REFERER="http://localhost/iframe"
        )

        self.assertEqual(resp['X-Frame-Options'], 'DENY')

        self.configure_lti_provider(name='Test', lti_hostname='localhost', lti_consumer_key='test_key', enabled=True)

        resp = self.client.get(
            reverse("register_user"),
            HTTP_REFERER="http://localhost/iframe"
        )

        self.assertEqual(resp['X-Frame-Options'], 'ALLOW')

    def _assert_third_party_auth_data(self, response, current_backend, current_provider, providers, expected_ec,
                                      add_user_details=False):
        """Verify that third party auth info is rendered correctly in a DOM data attribute. """
        finish_auth_url = None
        if current_backend:
            finish_auth_url = reverse("social:complete", kwargs={"backend": current_backend}) + "?"

        auth_info = {
            "currentProvider": current_provider,
            "providers": providers,
            "secondaryProviders": [],
            "finishAuthUrl": finish_auth_url,
            "errorMessage": None,
            "registerFormSubmitButtonText": "Create Account",
            "syncLearnerProfileData": False,
            "pipeline_user_details": {"email": "test@test.com"} if add_user_details else {}
        }
        if expected_ec is not None:
            # If we set an EnterpriseCustomer, third-party auth providers ought to be hidden.
            auth_info['providers'] = []
        auth_info = dump_js_escaped_json(auth_info)

        expected_data = '"third_party_auth": {auth_info}'.format(
            auth_info=auth_info
        )
        self.assertContains(response, expected_data)

    def _assert_saml_auth_data_with_error(
            self, response, current_backend, current_provider, expected_error_message
    ):
        """
        Verify that third party auth info is rendered correctly in a DOM data attribute.
        """
        finish_auth_url = None
        if current_backend:
            finish_auth_url = reverse('social:complete', kwargs={'backend': current_backend}) + '?'

        auth_info = {
            'currentProvider': current_provider,
            'providers': [],
            'secondaryProviders': [],
            'finishAuthUrl': finish_auth_url,
            'errorMessage': expected_error_message,
            'registerFormSubmitButtonText': 'Create Account',
            'syncLearnerProfileData': False,
            'pipeline_user_details': {'response': {'idp_name': 'testshib'}}
        }
        auth_info = dump_js_escaped_json(auth_info)

        expected_data = '"third_party_auth": {auth_info}'.format(
            auth_info=auth_info
        )
        self.assertContains(response, expected_data)

    def _third_party_login_url(self, backend_name, auth_entry, login_params):
        """Construct the login URL to start third party authentication. """
        return u"{url}?auth_entry={auth_entry}&{param_str}".format(
            url=reverse("social:begin", kwargs={"backend": backend_name}),
            auth_entry=auth_entry,
            param_str=self._finish_auth_url_param(login_params),
        )

    def _finish_auth_url_param(self, params):
        """
        Make the next=... URL parameter that indicates where the user should go next.

        >>> _finish_auth_url_param([('next', '/dashboard')])
        '/account/finish_auth?next=%2Fdashboard'
        """
        return urlencode({
            'next': '/account/finish_auth?{}'.format(urlencode(params))
        })

    def test_english_by_default(self):
        response = self.client.get(reverse('signin_user'), [], HTTP_ACCEPT="text/html")

        self.assertEqual(response['Content-Language'], 'en')

    def test_unsupported_language(self):
        response = self.client.get(reverse('signin_user'), [], HTTP_ACCEPT="text/html", HTTP_ACCEPT_LANGUAGE="ts-zx")

        self.assertEqual(response['Content-Language'], 'en')

    def test_browser_language(self):
        response = self.client.get(reverse('signin_user'), [], HTTP_ACCEPT="text/html", HTTP_ACCEPT_LANGUAGE="es")

        self.assertEqual(response['Content-Language'], 'es-419')

    def test_browser_language_dialent(self):
        response = self.client.get(reverse('signin_user'), [], HTTP_ACCEPT="text/html", HTTP_ACCEPT_LANGUAGE="es-es")

        self.assertEqual(response['Content-Language'], 'es-es')


@skip_unless_lms
class AccountCreationTestCaseWithSiteOverrides(SiteMixin, TestCase):
    """
    Test cases for Feature flag ALLOW_PUBLIC_ACCOUNT_CREATION which when
    turned off disables the account creation options in lms
    """

    def setUp(self):
        """Set up the tests"""
        super(AccountCreationTestCaseWithSiteOverrides, self).setUp()

        # Set the feature flag ALLOW_PUBLIC_ACCOUNT_CREATION to False
        self.site_configuration_values = {
            'ALLOW_PUBLIC_ACCOUNT_CREATION': False
        }
        self.site_domain = 'testserver1.com'
        self.set_up_site(self.site_domain, self.site_configuration_values)

    def test_register_option_login_page(self):
        """
        Navigate to the login page and check the Register option is hidden when
        ALLOW_PUBLIC_ACCOUNT_CREATION flag is turned off
        """
        response = self.client.get(reverse('signin_user'))
        self.assertNotIn('<a class="btn-neutral" href="/register?next=%2Fdashboard">Register</a>',
                         response.content)
