"""
Test the various password reset flows
"""


import json
import re
import unicodedata
import unittest

import ddt
from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, make_password
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN, PasswordResetConfirmView
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.cache import cache
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import int_to_base36
from mock import Mock, patch
from oauth2_provider import models as dot_models
from six.moves import range

from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.djangoapps.user_api.models import UserRetirementRequest
from openedx.core.djangoapps.user_api.tests.test_views import UserAPITestCase
from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH
from openedx.core.djangoapps.user_authn.views.password_reset import (
    SETTING_CHANGE_INITIATED, password_reset,
    PasswordResetConfirmWrapper)
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory
from student.tests.test_configuration_overrides import fake_get_value
from student.tests.test_email import mock_render_to_string

from util.password_policy_validators import create_validator_config
from util.testing import EventTestMixin


def process_request(request):
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()


@unittest.skipUnless(
    settings.ROOT_URLCONF == "lms.urls",
    "reset password tests should only run in LMS"
)
@ddt.ddt
class ResetPasswordTests(EventTestMixin, CacheIsolationTestCase):
    """
    Tests that clicking reset password sends email, and doesn't activate the user
    """
    request_factory = RequestFactory()
    ENABLED_CACHES = ['default']

    def setUp(self):  # pylint: disable=arguments-differ
        super(ResetPasswordTests, self).setUp('openedx.core.djangoapps.user_authn.views.password_reset.tracker')
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()
        self.token = default_token_generator.make_token(self.user)
        self.uidb36 = int_to_base36(self.user.id)

        self.user_bad_passwd = UserFactory.create()
        self.user_bad_passwd.is_active = False
        self.user_bad_passwd.password = UNUSABLE_PASSWORD_PREFIX
        self.user_bad_passwd.save()

    def setup_request_session_with_token(self, request):
        """
        Internal helper to setup request session and add token in session.
        """
        process_request(request)
        request.session[INTERNAL_RESET_SESSION_TOKEN] = self.token

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_user_bad_password_reset(self):
        """
        Tests password reset behavior for user with password marked UNUSABLE_PASSWORD_PREFIX
        """

        bad_pwd_req = self.request_factory.post('/password_reset/', {'email': self.user_bad_passwd.email})
        bad_pwd_req.user = AnonymousUser()
        bad_pwd_resp = password_reset(bad_pwd_req)
        # If they've got an unusable password, we return a successful response code
        self.assertEqual(bad_pwd_resp.status_code, 200)
        obj = json.loads(bad_pwd_resp.content.decode('utf-8'))
        self.assertEqual(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })
        self.assert_no_events_were_emitted()

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_nonexist_email_password_reset(self):
        """
        Now test the exception cases with of reset_password called with invalid email.
        """

        bad_email_req = self.request_factory.post('/password_reset/', {'email': self.user.email + "makeItFail"})
        bad_email_req.user = AnonymousUser()
        bad_email_resp = password_reset(bad_email_req)
        # Note: even if the email is bad, we return a successful response code
        # This prevents someone potentially trying to "brute-force" find out which
        # emails are and aren't registered with edX
        self.assertEqual(bad_email_resp.status_code, 200)
        obj = json.loads(bad_email_resp.content.decode('utf-8'))
        self.assertEqual(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })
        self.assert_no_events_were_emitted()

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_password_reset_ratelimited_for_non_existing_user(self):
        """
        Test that reset password endpoint only allow one request per minute
        for non-existing user.
        """
        self.assert_password_reset_ratelimitted('thisdoesnotexist@foo.com', AnonymousUser())
        self.assert_no_events_were_emitted()

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_password_reset_ratelimited_for_existing_user(self):
        """
        Test that reset password endpoint only allow one request per minute
        for existing user.
        """
        self.assert_password_reset_ratelimitted(self.user.email, self.user)
        self.assert_event_emission_count(SETTING_CHANGE_INITIATED, 1)

    def assert_password_reset_ratelimitted(self, email, user):
        """
        Assert that password reset endpoint allow one request per minute per email.
        """
        cache.clear()
        password_reset_req = self.request_factory.post('/password_reset/', {'email': email})
        password_reset_req.user = user
        password_reset_req.site = Mock(domain='example.com')
        good_resp = password_reset(password_reset_req)
        self.assertEqual(good_resp.status_code, 200)

        # then the rate limiter should kick in and give a HttpForbidden response
        bad_resp = password_reset(password_reset_req)
        self.assertEqual(bad_resp.status_code, 403)

        cache.clear()

    def test_ratelimitted_from_same_ip_with_different_email(self):
        """
        Test that password reset endpoint allow only one request per minute per IP.
        """
        cache.clear()
        good_req = self.request_factory.post('/password_reset/', {'email': 'thisdoesnotexist@foo.com'})
        good_req.user = AnonymousUser()
        good_resp = password_reset(good_req)
        self.assertEqual(good_resp.status_code, 200)

        # change the email ID and verify that the rate limiter should kick in and
        # give a Forbidden response if the request is from same IP.
        bad_req = self.request_factory.post('/password_reset/', {'email': 'thisdoesnotexist2@foo.com'})
        bad_req.user = AnonymousUser()
        bad_resp = password_reset(bad_req)
        self.assertEqual(bad_resp.status_code, 403)

        cache.clear()

    def test_ratelimited_from_different_ips_with_same_email(self):
        """
        Test that password reset endpoint allow only one request per minute
        per email address.
        """
        cache.clear()
        good_req = self.request_factory.post('/password_reset/', {'email': 'thisdoesnotexist@foo.com'})
        good_req.user = AnonymousUser()
        good_resp = password_reset(good_req)
        self.assertEqual(good_resp.status_code, 200)

        # change the IP and verify that the rate limiter should kick in and
        # give a Forbidden response if the request is for same email address.
        new_ip = "8.8.8.8"
        self.assertNotEqual(good_req.META.get('REMOTE_ADDR'), new_ip)

        bad_req = self.request_factory.post(
            '/password_reset/',
            {'email': 'thisdoesnotexist@foo.com'},
            REMOTE_ADDR=new_ip
        )
        bad_req.user = AnonymousUser()
        bad_resp = password_reset(bad_req)
        self.assertEqual(bad_resp.status_code, 403)
        self.assertEqual(bad_req.META.get('REMOTE_ADDR'), new_ip)

        cache.clear()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data(('plain_text', "You're receiving this e-mail because you requested a password reset"),
              ('html', "You&#39;re receiving this e-mail because you requested a password reset"))
    @ddt.unpack
    def test_reset_password_email(self, body_type, expected_output):
        """Tests contents of reset password email, and that user is not active"""
        good_req = self.request_factory.post('/password_reset/', {'email': self.user.email})
        good_req.user = self.user
        good_req.site = Mock(domain='example.com')
        dot_application = dot_factories.ApplicationFactory(user=self.user)
        dot_access_token = dot_factories.AccessTokenFactory(user=self.user, application=dot_application)
        dot_factories.RefreshTokenFactory(user=self.user, application=dot_application, access_token=dot_access_token)
        good_resp = password_reset(good_req)
        self.assertEqual(good_resp.status_code, 200)
        self.assertFalse(dot_models.AccessToken.objects.filter(user=self.user).exists())
        self.assertFalse(dot_models.RefreshToken.objects.filter(user=self.user).exists())
        obj = json.loads(good_resp.content.decode('utf-8'))
        self.assertTrue(obj['success'])
        self.assertIn('e-mailed you instructions for setting your password', obj['value'])

        from_email = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        sent_message = mail.outbox[0]

        bodies = {
            'plain_text': sent_message.body,
            'html': sent_message.alternatives[0][0],
        }

        body = bodies[body_type]

        self.assertIn("Password reset", sent_message.subject)
        self.assertIn(expected_output, body)
        self.assertEqual(sent_message.from_email, from_email)
        self.assertEqual(len(sent_message.to), 1)
        self.assertIn(self.user.email, sent_message.to)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None,
        )

        # Test that the user is not active
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

        self.assertIn('password_reset_confirm/', body)
        re.search(r'password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/', body).groupdict()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data((False, 'http://'), (True, 'https://'))
    @ddt.unpack
    def test_reset_password_email_https(self, is_secure, protocol):
        """
        Tests that the right url protocol is included in the reset password link
        """
        req = self.request_factory.post(
            '/password_reset/', {'email': self.user.email}
        )
        req.site = Mock(domain='example.com')
        req.is_secure = Mock(return_value=is_secure)
        req.user = self.user
        password_reset(req)
        sent_message = mail.outbox[0]
        msg = sent_message.body
        expected_msg = "Please go to the following page and choose a new password:\n\n" + protocol

        self.assertIn(expected_msg, msg)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
        )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data(('Crazy Awesome Site', 'Crazy Awesome Site'), ('edX', 'edX'))
    @ddt.unpack
    def test_reset_password_email_site(self, site_name, platform_name):
        """
        Tests that the right url domain and platform name is included in
        the reset password email
        """
        with patch("django.conf.settings.PLATFORM_NAME", platform_name):
            with patch("django.conf.settings.SITE_NAME", site_name):
                req = self.request_factory.post(
                    '/password_reset/', {'email': self.user.email}
                )
                req.user = self.user
                req.site = Mock(domain='example.com')
                password_reset(req)
                sent_message = mail.outbox[0]
                msg = sent_message.body

                reset_msg = u"you requested a password reset for your user account at {}"
                reset_msg = reset_msg.format(site_name)

                self.assertIn(reset_msg, msg)

                sign_off = u"The {} Team".format(platform_name)
                self.assertIn(sign_off, msg)

                self.assert_event_emitted(
                    SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
                )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    @ddt.data('plain_text', 'html')
    def test_reset_password_email_configuration_override(self, body_type):
        """
        Tests that the right url domain and platform name is included in
        the reset password email
        """
        req = self.request_factory.post(
            '/password_reset/', {'email': self.user.email}
        )
        req.get_host = Mock(return_value=None)
        req.site = Mock(domain='example.com')
        req.user = self.user

        with patch('crum.get_current_request', return_value=req):
            password_reset(req)

        sent_message = mail.outbox[0]
        bodies = {
            'plain_text': sent_message.body,
            'html': sent_message.alternatives[0][0],
        }

        body = bodies[body_type]

        reset_msg = u"you requested a password reset for your user account at {}".format(
            fake_get_value('PLATFORM_NAME')
        )

        self.assertIn(reset_msg, body)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
        )
        self.assertEqual(sent_message.from_email, "no-reply@fakeuniversity.com")

    @ddt.data(
        ('invalidUid', 'invalid_token'),
        (None, 'invalid_token'),
        ('invalidUid', None),
    )
    @ddt.unpack
    def test_reset_password_bad_token(self, uidb36, token):
        """
        Tests bad token and uidb36 in password reset
        """
        if uidb36 is None:
            uidb36 = self.uidb36
        if token is None:
            token = self.token

        bad_request = self.request_factory.get(
            reverse(
                "password_reset_confirm",
                kwargs={"uidb36": uidb36, "token": token}
            )
        )
        process_request(bad_request)
        bad_request.user = AnonymousUser()
        PasswordResetConfirmWrapper.as_view()(bad_request, uidb36=uidb36, token=token)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

    def test_reset_password_good_token(self):
        """
        Tests good token and uidb36 in password reset.

        Scenario:
        When the password reset url is opened
        Then the page is redirected to url without token
        And token gets set in session
        When the redirected page is visited with token in session
        Then reset password page renders
        And inactive user is set to active
        """
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )
        good_reset_req = self.request_factory.get(url)
        process_request(good_reset_req)
        good_reset_req.user = self.user
        redirect_response = PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token=self.token)

        good_reset_req = self.request_factory.get(redirect_response.url)
        self.setup_request_session_with_token(good_reset_req)
        good_reset_req.user = self.user
        # set-password is the new token representation in the redirect url
        PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token='set-password')

        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    def test_reset_password_good_token_with_anonymous_user(self):
        """
        Tests good token and uidb36 in password reset for anonymous user.

        Scenario:
        When the password reset url is opened with anonymous user in request
        Then the page is redirected to url without token
        And token gets set in session
        When the redirected page is visited with token in session
        Then reset password page renders
        And inactive user associated with token is set to active
        """
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )
        good_reset_req = self.request_factory.get(url)
        process_request(good_reset_req)
        good_reset_req.user = AnonymousUser()
        redirect_response = PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token=self.token)

        good_reset_req = self.request_factory.get(redirect_response.url)
        self.setup_request_session_with_token(good_reset_req)
        good_reset_req.user = AnonymousUser()
        # set-password is the new token representation in the redirect url
        PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token='set-password')

        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    def test_password_reset_fail(self):
        """
        Tests that if we provide mismatched passwords, user is not marked as active.
        """
        self.assertFalse(self.user.is_active)

        url = reverse(
            'password_reset_confirm',
            kwargs={'uidb36': self.uidb36, 'token': self.token}
        )
        request_params = {'new_password1': 'password1', 'new_password2': 'password2'}
        confirm_request = self.request_factory.post(url, data=request_params)
        self.setup_request_session_with_token(confirm_request)
        confirm_request.user = self.user

        # Make a password reset request with mismatching passwords.
        resp = PasswordResetConfirmWrapper.as_view()(confirm_request, uidb36=self.uidb36, token=self.token)

        # Verify the response status code is: 200 with password reset fail and also verify that
        # the user is not marked as active.
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    def test_password_reset_retired_user_fail(self):
        """
        Tests that if a retired user attempts to reset their password, it fails.
        """
        self.assertFalse(self.user.is_active)

        # Retire the user.
        UserRetirementRequest.create_retirement_request(self.user)

        url = reverse(
            'password_reset_confirm',
            kwargs={'uidb36': self.uidb36, 'token': self.token}
        )
        reset_req = self.request_factory.get(url)
        reset_req.user = self.user
        resp = PasswordResetConfirmWrapper.as_view()(reset_req, uidb36=self.uidb36, token=self.token)

        # Verify the response status code is: 200 with password reset fail and also verify that
        # the user is not marked as active.
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    def test_password_reset_normalize_password(self):
        # pylint: disable=anomalous-unicode-escape-in-string
        """
        Tests that if we provide a not properly normalized password, it is saved using our normalization
        method of NFKC.
        In this test, the input password is u'p\u212bssword'. It should be normalized to u'p\xc5ssword'
        """
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )

        password = u'p\u212bssword'
        request_params = {'new_password1': password, 'new_password2': password}
        confirm_request = self.request_factory.post(url, data=request_params)
        process_request(confirm_request)
        confirm_request.session[INTERNAL_RESET_SESSION_TOKEN] = self.token
        confirm_request.user = self.user
        __ = PasswordResetConfirmWrapper.as_view()(confirm_request, uidb36=self.uidb36, token=self.token)

        user = User.objects.get(pk=self.user.pk)
        salt_val = user.password.split('$')[1]
        expected_user_password = make_password(unicodedata.normalize('NFKC', u'p\u212bssword'), salt_val)
        self.assertEqual(expected_user_password, user.password)

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 2}),
        create_validator_config('util.password_policy_validators.MaximumLengthValidator', {'max_length': 10})
    ])
    @ddt.data(
        {
            'password': '1',
            'error_message': 'This password is too short. It must contain at least 2 characters.',
        },
        {
            'password': '01234567891',
            'error_message': 'This password is too long. It must contain no more than 10 characters.',
        }
    )
    def test_password_reset_with_invalid_length(self, password_dict):
        """
        Tests that if we provide password characters less then PASSWORD_MIN_LENGTH,
        or more than PASSWORD_MAX_LENGTH, password reset will fail with error message.
        """

        url = reverse(
            'password_reset_confirm',
            kwargs={'uidb36': self.uidb36, 'token': self.token}
        )
        request_params = {'new_password1': password_dict['password'], 'new_password2': password_dict['password']}
        confirm_request = self.request_factory.post(url, data=request_params)
        self.setup_request_session_with_token(confirm_request)
        confirm_request.user = self.user

        # Make a password reset request with minimum/maximum passwords characters.
        response = PasswordResetConfirmWrapper.as_view()(confirm_request, uidb36=self.uidb36, token=self.token)

        self.assertEqual(response.context_data['err_msg'], password_dict['error_message'])

    @patch.object(PasswordResetConfirmView, 'dispatch')
    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    def test_reset_password_good_token_configuration_override(self, reset_confirm):
        """
        Tests password reset confirmation page for site configuration override.
        """
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )
        good_reset_req = self.request_factory.get(url)
        process_request(good_reset_req)
        good_reset_req.user = self.user
        PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token=self.token)
        confirm_kwargs = reset_confirm.call_args[1]
        self.assertEqual(confirm_kwargs['extra_context']['platform_name'], 'Fake University')
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data('Crazy Awesome Site', 'edX')
    def test_reset_password_email_subject(self, platform_name):
        """
        Tests that the right platform name is included in
        the reset password email subject
        """
        with patch("django.conf.settings.PLATFORM_NAME", platform_name):
            req = self.request_factory.post(
                '/password_reset/', {'email': self.user.email}
            )
            req.user = self.user
            req.site = Mock(domain='example.com')
            password_reset(req)
            sent_message = mail.outbox[0]
            subj = sent_message.subject

            self.assertIn(platform_name, subj)

    def test_reset_password_with_other_user_link(self):
        """
        Tests that user should not be able to reset password through other user's token
        """
        reset_url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )
        reset_request = self.request_factory.get(reset_url)
        reset_request.user = UserFactory.create()

        self.assertRaises(Http404, PasswordResetConfirmWrapper.as_view(), reset_request, uidb36=self.uidb36,
                          token=self.token)


@ddt.ddt
@skip_unless_lms
class PasswordResetViewTest(UserAPITestCase):
    """Tests of the user API's password reset endpoint. """

    def setUp(self):
        super(PasswordResetViewTest, self).setUp()
        self.url = reverse("user_api_password_reset")

    @ddt.data("get", "post")
    def test_auth_disabled(self, method):
        self.assertAuthDisabled(method, self.url)

    def test_allowed_methods(self):
        self.assertAllowedMethods(self.url, ["GET", "HEAD", "OPTIONS"])

    def test_put_not_allowed(self):
        response = self.client.put(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_patch_not_allowed(self):
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_password_reset_form(self):
        # Retrieve the password reset form
        response = self.client.get(self.url, content_type="application/json")
        self.assertHttpOK(response)

        # Verify that the form description matches what we expect
        form_desc = json.loads(response.content.decode('utf-8'))
        self.assertEqual(form_desc["method"], "post")
        self.assertEqual(form_desc["submit_url"], reverse("password_change_request"))
        self.assertEqual(form_desc["fields"], [
            {
                "name": "email",
                "defaultValue": "",
                "type": "email",
                "required": True,
                "label": "Email",
                "placeholder": "username@domain.com",
                "instructions": u"The email address you used to register with {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                "restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            }
        ])
