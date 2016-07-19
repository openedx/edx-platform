# -*- coding: utf-8 -*-
""" Tests for student account views. """

from copy import copy
import re
from unittest import skipUnless
from urllib import urlencode

import mock
import ddt
from django.conf import settings
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.messages.middleware import MessageMiddleware
from django.test import TestCase
from django.test.utils import override_settings
from django.http import HttpRequest
from edx_rest_api_client import exceptions
from nose.plugins.attrib import attr

from commerce.models import CommerceConfiguration
from commerce.tests import TEST_API_URL, TEST_API_SIGNING_KEY, factories
from commerce.tests.mocks import mock_get_orders
from course_modes.models import CourseMode
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin
from openedx.core.djangoapps.user_api.accounts.api import activate_account, create_account
from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH
from openedx.core.djangolib.js_utils import dump_js_escaped_json
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory
from student_account.views import account_settings_context, get_user_orders
from third_party_auth.tests.testutil import simulate_running_pipeline, ThirdPartyAuthTestMixin
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme_context


@ddt.ddt
class StudentAccountUpdateTest(CacheIsolationTestCase, UrlResetMixin):
    """ Tests for the student account views that update the user's account information. """

    USERNAME = u"heisenberg"
    ALTERNATE_USERNAME = u"walt"
    OLD_PASSWORD = u"ḅḷüëṡḳÿ"
    NEW_PASSWORD = u"🄱🄸🄶🄱🄻🅄🄴"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

    INVALID_ATTEMPTS = 100

    INVALID_EMAILS = [
        None,
        u"",
        u"a",
        "no_domain",
        "no+domain",
        "@",
        "@domain.com",
        "test@no_extension",

        # Long email -- subtract the length of the @domain
        # except for one character (so we exceed the max length limit)
        u"{user}@example.com".format(
            user=(u'e' * (EMAIL_MAX_LENGTH - 11))
        )
    ]

    INVALID_KEY = u"123abc"

    URLCONF_MODULES = ['student_accounts.urls']

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(StudentAccountUpdateTest, self).setUp()

        # Create/activate a new account
        activation_key = create_account(self.USERNAME, self.OLD_PASSWORD, self.OLD_EMAIL)
        activate_account(activation_key)

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
        result = re.search('(?P<url>https?://[^\s]+)', email_body)
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
        response = self.client.post(
            activation_link,
            {'new_password1': self.OLD_PASSWORD, 'new_password2': self.OLD_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This password reset link is invalid. It may have been used already.")

        self.client.logout()

        # Verify that the old password cannot be used to log in
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertFalse(result)

        # Verify that the new password continues to be valid
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)

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

        # Send the view an email address not tied to any user
        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 400)

    def test_password_change_rate_limited(self):
        # Log out the user created during test setup, to prevent the view from
        # selecting the logged-in user's email address over the email provided
        # in the POST data
        self.client.logout()

        # Make many consecutive bad requests in an attempt to trigger the rate limiter
        for attempt in xrange(self.INVALID_ATTEMPTS):
            self._change_password(email=self.NEW_EMAIL)

        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 403)

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

    def _change_password(self, email=None):
        """Request to change the user's password. """
        data = {}

        if email:
            data['email'] = email

        return self.client.post(path=reverse('password_change_request'), data=data)


@attr('shard_3')
@ddt.ddt
class StudentAccountLoginAndRegistrationTest(ThirdPartyAuthTestMixin, UrlResetMixin, ModuleStoreTestCase):
    """ Tests for the student account views that update the user's account information. """

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"

    URLCONF_MODULES = ['embargo']

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(StudentAccountLoginAndRegistrationTest, self).setUp()

        # For these tests, three third party auth providers are enabled by default:
        self.configure_google_provider(enabled=True)
        self.configure_facebook_provider(enabled=True)
        self.configure_dummy_provider(
            enabled=True,
            icon_class='',
            icon_image=SimpleUploadedFile('icon.svg', '<svg><rect width="50" height="100"/></svg>'),
        )

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
        # Create/activate a new account and log in
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        activate_account(activation_key)
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
    def test_login_and_registration_form_signin_preserves_params(self, theme, url_name):
        params = [
            ('course_id', 'edX/DemoX/Demo_Course'),
            ('enrollment_action', 'enroll'),
        ]

        # The response should have a "Sign In" button with the URL
        # that preserves the querystring params
        with with_comprehensive_theme_context(theme):
            response = self.client.get(reverse(url_name), params)

        expected_url = '/login?{}'.format(self._finish_auth_url_param(params + [('next', '/dashboard')]))
        self.assertContains(response, expected_url)

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
            response = self.client.get(reverse(url_name), params)

        expected_url = '/login?{}'.format(self._finish_auth_url_param(params))
        self.assertContains(response, expected_url)

    @mock.patch.dict(settings.FEATURES, {"ENABLE_THIRD_PARTY_AUTH": False})
    @ddt.data("signin_user", "register_user")
    def test_third_party_auth_disabled(self, url_name):
        response = self.client.get(reverse(url_name))
        self._assert_third_party_auth_data(response, None, None, [])

    @ddt.data(
        ("signin_user", None, None),
        ("register_user", None, None),
        ("signin_user", "google-oauth2", "Google"),
        ("register_user", "google-oauth2", "Google"),
        ("signin_user", "facebook", "Facebook"),
        ("register_user", "facebook", "Facebook"),
        ("signin_user", "dummy", "Dummy"),
        ("register_user", "dummy", "Dummy"),
    )
    @ddt.unpack
    def test_third_party_auth(self, url_name, current_backend, current_provider):
        params = [
            ('course_id', 'course-v1:Org+Course+Run'),
            ('enrollment_action', 'enroll'),
            ('course_mode', CourseMode.DEFAULT_MODE_SLUG),
            ('email_opt_in', 'true'),
            ('next', '/custom/final/destination'),
        ]

        # Simulate a running pipeline
        if current_backend is not None:
            pipeline_target = "student_account.views.third_party_auth.pipeline"
            with simulate_running_pipeline(pipeline_target, current_backend):
                response = self.client.get(reverse(url_name), params)

        # Do NOT simulate a running pipeline
        else:
            response = self.client.get(reverse(url_name), params)

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
        self._assert_third_party_auth_data(response, current_backend, current_provider, expected_providers)

    def test_hinted_login(self):
        params = [("next", "/courses/something/?tpa_hint=oa2-google-oauth2")]
        response = self.client.get(reverse('signin_user'), params)
        self.assertContains(response, '"third_party_auth_hint": "oa2-google-oauth2"')

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_microsite_uses_old_login_page(self):
        # Retrieve the login page from a microsite domain
        # and verify that we're served the old page.
        resp = self.client.get(
            reverse("signin_user"),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME
        )
        self.assertContains(resp, "Log into your Test Site Account")
        self.assertContains(resp, "login-form")

    def test_microsite_uses_old_register_page(self):
        # Retrieve the register page from a microsite domain
        # and verify that we're served the old page.
        resp = self.client.get(
            reverse("register_user"),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME
        )
        self.assertContains(resp, "Register for Test Site")
        self.assertContains(resp, "register-form")

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

    def _assert_third_party_auth_data(self, response, current_backend, current_provider, providers):
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


@override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
class AccountSettingsViewTest(ThirdPartyAuthTestMixin, TestCase, ProgramsApiConfigMixin):
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
    ]

    HIDDEN_FIELDS = [
        'time_zone',
    ]

    @mock.patch("django.conf.settings.MESSAGE_STORAGE", 'django.contrib.messages.storage.cookie.CookieStorage')
    def setUp(self):
        super(AccountSettingsViewTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        CommerceConfiguration.objects.create(cache_ttl=10, enabled=True)
        self.client.login(username=self.USERNAME, password=self.PASSWORD)

        self.request = HttpRequest()
        self.request.user = self.user

        # For these tests, two third party auth providers are enabled by default:
        self.configure_google_provider(enabled=True)
        self.configure_facebook_provider(enabled=True)

        # Python-social saves auth failure notifcations in Django messages.
        # See pipeline.get_duplicate_provider() for details.
        self.request.COOKIES = {}
        MessageMiddleware().process_request(self.request)
        messages.error(self.request, 'Facebook is already in use.', extra_tags='Auth facebook')

    def test_context(self):

        context = account_settings_context(self.request)

        user_accounts_api_url = reverse("accounts_api", kwargs={'username': self.user.username})
        self.assertEqual(context['user_accounts_api_url'], user_accounts_api_url)

        user_preferences_api_url = reverse('preferences_api', kwargs={'username': self.user.username})
        self.assertEqual(context['user_preferences_api_url'], user_preferences_api_url)

        for attribute in self.FIELDS:
            self.assertIn(attribute, context['fields'])

        self.assertEqual(
            context['user_accounts_api_url'], reverse("accounts_api", kwargs={'username': self.user.username})
        )
        self.assertEqual(
            context['user_preferences_api_url'], reverse('preferences_api', kwargs={'username': self.user.username})
        )

        self.assertEqual(context['duplicate_provider'], 'facebook')
        self.assertEqual(context['auth']['providers'][0]['name'], 'Facebook')
        self.assertEqual(context['auth']['providers'][1]['name'], 'Google')

    def test_hidden_fields_not_visible(self):
        """
        Test that hidden fields are not visible when disabled.
        """
        temp_features = copy(settings.FEATURES)
        temp_features['ENABLE_TIME_ZONE_PREFERENCE'] = False
        with self.settings(FEATURES=temp_features):
            view_path = reverse('account_settings')
            response = self.client.get(path=view_path)

            for attribute in self.FIELDS:
                self.assertIn(attribute, response.content)
            for attribute in self.HIDDEN_FIELDS:
                self.assertIn('"%s": {"enabled": false' % (attribute), response.content)

    def test_hidden_fields_are_visible(self):
        """
        Test that hidden fields are visible when enabled.
        """
        temp_features = copy(settings.FEATURES)
        temp_features['ENABLE_TIME_ZONE_PREFERENCE'] = True
        with self.settings(FEATURES=temp_features):
            view_path = reverse('account_settings')
            response = self.client.get(path=view_path)

            for attribute in self.FIELDS:
                self.assertIn(attribute, response.content)
            for attribute in self.HIDDEN_FIELDS:
                self.assertIn('"%s": {"enabled": true' % (attribute), response.content)

    def test_header_with_programs_listing_enabled(self):
        """
        Verify that tabs header will be shown while program listing is enabled.
        """
        self.create_programs_config(program_listing_enabled=True)
        view_path = reverse('account_settings')
        response = self.client.get(path=view_path)

        self.assertContains(response, '<li class="tab-nav-item">')

    def test_header_with_programs_listing_disabled(self):
        """
        Verify that nav header will be shown while program listing is disabled.
        """
        self.create_programs_config(program_listing_enabled=False)
        view_path = reverse('account_settings')
        response = self.client.get(path=view_path)

        self.assertContains(response, '<li class="item nav-global-01">')

    def test_commerce_order_detail(self):
        with mock_get_orders():
            order_detail = get_user_orders(self.user)

        user_order = mock_get_orders.default_response['results'][0]
        expected = [
            {
                'number': user_order['number'],
                'price': user_order['total_excl_tax'],
                'title': user_order['lines'][0]['title'],
                'order_date': 'Jan 01, 2016',
                'receipt_url': '/commerce/checkout/receipt/?orderNum=' + user_order['number']
            }
        ]
        self.assertEqual(order_detail, expected)

    def test_commerce_order_detail_exception(self):
        with mock_get_orders(exception=exceptions.HttpNotFoundError):
            order_detail = get_user_orders(self.user)

        self.assertEqual(order_detail, [])

    def test_incomplete_order_detail(self):
        response = {
            'results': [
                factories.OrderFactory(
                    status='Incomplete',
                    lines=[
                        factories.OrderLineFactory(
                            product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory()])
                        )
                    ]
                )
            ]
        }
        with mock_get_orders(response=response):
            order_detail = get_user_orders(self.user)

        self.assertEqual(order_detail, [])

    def test_honor_course_order_detail(self):
        response = {
            'results': [
                factories.OrderFactory(
                    lines=[
                        factories.OrderLineFactory(
                            product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory(
                                name='certificate_type',
                                value='honor'
                            )])
                        )
                    ]
                )
            ]
        }
        with mock_get_orders(response=response):
            order_detail = get_user_orders(self.user)

        self.assertEqual(order_detail, [])

    def test_order_history_with_no_product(self):
        response = {
            'results': [
                factories.OrderFactory(
                    lines=[
                        factories.OrderLineFactory(
                            product=None
                        ),
                        factories.OrderLineFactory(
                            product=factories.ProductFactory(attribute_values=[factories.ProductAttributeFactory(
                                name='certificate_type',
                                value='verified'
                            )])
                        )
                    ]
                )
            ]
        }
        with mock_get_orders(response=response):
            order_detail = get_user_orders(self.user)

        self.assertEqual(len(order_detail), 1)


@override_settings(SITE_NAME=settings.MICROSITE_LOGISTRATION_HOSTNAME)
class MicrositeLogistrationTests(TestCase):
    """
    Test to validate that microsites can display the logistration page
    """

    def test_login_page(self):
        """
        Make sure that we get the expected logistration page on our specialized
        microsite
        """

        resp = self.client.get(
            reverse('signin_user'),
            HTTP_HOST=settings.MICROSITE_LOGISTRATION_HOSTNAME
        )
        self.assertEqual(resp.status_code, 200)

        self.assertIn('<div id="login-and-registration-container"', resp.content)

    def test_registration_page(self):
        """
        Make sure that we get the expected logistration page on our specialized
        microsite
        """

        resp = self.client.get(
            reverse('register_user'),
            HTTP_HOST=settings.MICROSITE_LOGISTRATION_HOSTNAME
        )
        self.assertEqual(resp.status_code, 200)

        self.assertIn('<div id="login-and-registration-container"', resp.content)

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_no_override(self):
        """
        Make sure we get the old style login/registration if we don't override
        """

        resp = self.client.get(
            reverse('signin_user'),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME
        )
        self.assertEqual(resp.status_code, 200)

        self.assertNotIn('<div id="login-and-registration-container"', resp.content)

        resp = self.client.get(
            reverse('register_user'),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME
        )
        self.assertEqual(resp.status_code, 200)

        self.assertNotIn('<div id="login-and-registration-container"', resp.content)
