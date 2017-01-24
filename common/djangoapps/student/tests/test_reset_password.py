"""
Test the various password reset flows
"""
import json
import re
import unittest

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.tokens import default_token_generator
from edx_oauth2_provider.tests.factories import ClientFactory, AccessTokenFactory, RefreshTokenFactory
from oauth2_provider import models as dot_models
from provider.oauth2 import models as dop_models

from django.utils.http import int_to_base36

from mock import Mock, patch
import ddt

from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.views import password_reset, password_reset_confirm_wrapper, SETTING_CHANGE_INITIATED
from student.tests.factories import UserFactory
from student.tests.test_email import mock_render_to_string
from util.testing import EventTestMixin

from .test_configuration_overrides import fake_get_value
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


@unittest.skipUnless(
    settings.ROOT_URLCONF == "lms.urls",
    "reset password tests should only run in LMS"
)
@ddt.ddt
class ResetPasswordTests(EventTestMixin, CacheIsolationTestCase):
    """ Tests that clicking reset password sends email, and doesn't activate the user
    """
    request_factory = RequestFactory()

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(ResetPasswordTests, self).setUp('student.views.tracker')
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()
        self.token = default_token_generator.make_token(self.user)
        self.uidb36 = int_to_base36(self.user.id)

        self.user_bad_passwd = UserFactory.create()
        self.user_bad_passwd.is_active = False
        self.user_bad_passwd.password = UNUSABLE_PASSWORD_PREFIX
        self.user_bad_passwd.save()

    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_user_bad_password_reset(self):
        """Tests password reset behavior for user with password marked UNUSABLE_PASSWORD_PREFIX"""

        bad_pwd_req = self.request_factory.post('/password_reset/', {'email': self.user_bad_passwd.email})
        bad_pwd_resp = password_reset(bad_pwd_req)
        # If they've got an unusable password, we return a successful response code
        self.assertEquals(bad_pwd_resp.status_code, 200)
        obj = json.loads(bad_pwd_resp.content)
        self.assertEquals(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })
        self.assert_no_events_were_emitted()

    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_nonexist_email_password_reset(self):
        """Now test the exception cases with of reset_password called with invalid email."""

        bad_email_req = self.request_factory.post('/password_reset/', {'email': self.user.email + "makeItFail"})
        bad_email_resp = password_reset(bad_email_req)
        # Note: even if the email is bad, we return a successful response code
        # This prevents someone potentially trying to "brute-force" find out which
        # emails are and aren't registered with edX
        self.assertEquals(bad_email_resp.status_code, 200)
        obj = json.loads(bad_email_resp.content)
        self.assertEquals(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })
        self.assert_no_events_were_emitted()

    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_password_reset_ratelimited(self):
        """ Try (and fail) resetting password 30 times in a row on an non-existant email address """
        cache.clear()

        for i in xrange(30):
            good_req = self.request_factory.post('/password_reset/', {
                'email': 'thisdoesnotexist{0}@foo.com'.format(i)
            })
            good_resp = password_reset(good_req)
            self.assertEquals(good_resp.status_code, 200)

        # then the rate limiter should kick in and give a HttpForbidden response
        bad_req = self.request_factory.post('/password_reset/', {'email': 'thisdoesnotexist@foo.com'})
        bad_resp = password_reset(bad_req)
        self.assertEquals(bad_resp.status_code, 403)
        self.assert_no_events_were_emitted()

        cache.clear()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_reset_password_email(self, send_email):
        """Tests contents of reset password email, and that user is not active"""

        good_req = self.request_factory.post('/password_reset/', {'email': self.user.email})
        good_req.user = self.user
        dop_client = ClientFactory()
        dop_access_token = AccessTokenFactory(user=self.user, client=dop_client)
        RefreshTokenFactory(user=self.user, client=dop_client, access_token=dop_access_token)
        dot_application = dot_factories.ApplicationFactory(user=self.user)
        dot_access_token = dot_factories.AccessTokenFactory(user=self.user, application=dot_application)
        dot_factories.RefreshTokenFactory(user=self.user, application=dot_application, access_token=dot_access_token)
        good_resp = password_reset(good_req)
        self.assertEquals(good_resp.status_code, 200)
        self.assertFalse(dop_models.AccessToken.objects.filter(user=self.user).exists())
        self.assertFalse(dop_models.RefreshToken.objects.filter(user=self.user).exists())
        self.assertFalse(dot_models.AccessToken.objects.filter(user=self.user).exists())
        self.assertFalse(dot_models.RefreshToken.objects.filter(user=self.user).exists())
        obj = json.loads(good_resp.content)
        self.assertEquals(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })

        (subject, msg, from_addr, to_addrs) = send_email.call_args[0]
        self.assertIn("Password reset", subject)
        self.assertIn("You're receiving this e-mail because you requested a password reset", msg)
        self.assertEquals(from_addr, configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL))
        self.assertEquals(len(to_addrs), 1)
        self.assertIn(self.user.email, to_addrs)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None,
        )

        #test that the user is not active
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)
        re.search(r'password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/', msg).groupdict()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @patch('django.core.mail.send_mail')
    @ddt.data((False, 'http://'), (True, 'https://'))
    @ddt.unpack
    def test_reset_password_email_https(self, is_secure, protocol, send_email):
        """
        Tests that the right url protocol is included in the reset password link
        """
        req = self.request_factory.post(
            '/password_reset/', {'email': self.user.email}
        )
        req.is_secure = Mock(return_value=is_secure)
        req.user = self.user
        password_reset(req)
        _, msg, _, _ = send_email.call_args[0]
        expected_msg = "Please go to the following page and choose a new password:\n\n" + protocol

        self.assertIn(expected_msg, msg)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
        )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @patch('django.core.mail.send_mail')
    @ddt.data(('Crazy Awesome Site', 'Crazy Awesome Site'), (None, 'edX'))
    @ddt.unpack
    def test_reset_password_email_domain(self, domain_override, platform_name, send_email):
        """
        Tests that the right url domain and platform name is included in
        the reset password email
        """
        with patch("django.conf.settings.PLATFORM_NAME", platform_name):
            req = self.request_factory.post(
                '/password_reset/', {'email': self.user.email}
            )
            req.get_host = Mock(return_value=domain_override)
            req.user = self.user
            password_reset(req)
            _, msg, _, _ = send_email.call_args[0]

            reset_msg = "you requested a password reset for your user account at {}"
            if domain_override:
                reset_msg = reset_msg.format(domain_override)
            else:
                reset_msg = reset_msg.format(settings.SITE_NAME)

            self.assertIn(reset_msg, msg)

            sign_off = "The {} Team".format(platform_name)
            self.assertIn(sign_off, msg)

            self.assert_event_emitted(
                SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
            )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    @patch('django.core.mail.send_mail')
    def test_reset_password_email_configuration_override(self, send_email):
        """
        Tests that the right url domain and platform name is included in
        the reset password email
        """
        req = self.request_factory.post(
            '/password_reset/', {'email': self.user.email}
        )
        req.get_host = Mock(return_value=None)
        req.user = self.user
        password_reset(req)
        _, msg, from_addr, _ = send_email.call_args[0]

        reset_msg = "you requested a password reset for your user account at openedx.localhost"

        self.assertIn(reset_msg, msg)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
        )
        self.assertEqual(from_addr, "no-reply@fakeuniversity.com")

    @ddt.data(
        ('invalidUid', 'invalid_token'),
        (None, 'invalid_token'),
        ('invalidUid', None),
    )
    @ddt.unpack
    def test_reset_password_bad_token(self, uidb36, token):
        """Tests bad token and uidb36 in password reset"""
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
        password_reset_confirm_wrapper(bad_request, uidb36, token)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

    def test_reset_password_good_token(self):
        """Tests good token and uidb36 in password reset"""
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )
        good_reset_req = self.request_factory.get(url)
        password_reset_confirm_wrapper(good_reset_req, self.uidb36, self.token)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    def test_password_reset_fail(self):
        """Tests that if we provide mismatched passwords, user is not marked as active."""
        self.assertFalse(self.user.is_active)

        url = reverse(
            'password_reset_confirm',
            kwargs={'uidb36': self.uidb36, 'token': self.token}
        )
        request_params = {'new_password1': 'password1', 'new_password2': 'password2'}
        confirm_request = self.request_factory.post(url, data=request_params)

        # Make a password reset request with mismatching passwords.
        resp = password_reset_confirm_wrapper(confirm_request, self.uidb36, self.token)

        # Verify the response status code is: 200 with password reset fail and also verify that
        # the user is not marked as active.
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    @patch('student.views.password_reset_confirm')
    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    def test_reset_password_good_token_configuration_override(self, reset_confirm):
        """Tests password reset confirmation page for site configuration override."""
        url = reverse(
            "password_reset_confirm",
            kwargs={"uidb36": self.uidb36, "token": self.token}
        )
        good_reset_req = self.request_factory.get(url)
        password_reset_confirm_wrapper(good_reset_req, self.uidb36, self.token)
        confirm_kwargs = reset_confirm.call_args[1]
        self.assertEquals(confirm_kwargs['extra_context']['platform_name'], 'Fake University')
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)
