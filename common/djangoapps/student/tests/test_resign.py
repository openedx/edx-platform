"""
Test the various resignation flows
"""
import json
import re
import unittest

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.utils.http import int_to_base36

from mock import Mock, patch
from textwrap import dedent

from student.models import UserStanding
from student.views import resign, resign_confirm
from student.tests.factories import UserFactory
from student.tests.test_email import mock_render_to_string


class ResignTests(TestCase):
    """
    Tests for resignation functionality
    """
    request_factory = RequestFactory()

    def setUp(self):
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()
        self.token = default_token_generator.make_token(self.user)
        self.uidb36 = int_to_base36(self.user.id)
        self.resign_reason = 'a' * 1000

    def test_resign_404(self):
        """Ensures that no get request to /resign/ is allowed"""

        bad_req = self.request_factory.get('/resign/')
        self.assertRaises(Http404, resign, bad_req)

    def test_resign_by_nonexist_email_user(self):
        """Now test the exception cases with of resign called with invalid email."""

        bad_email_req = self.request_factory.post('/resign/', {'email': self.user.email + "makeItFail"})
        bad_email_resp = resign(bad_email_req)
        # Note: even if the email is bad, we return a successful response code
        # This prevents someone potentially trying to "brute-force" find out which emails are and aren't registered with edX
        self.assertEquals(bad_email_resp.status_code, 200)
        obj = json.loads(bad_email_resp.content)
        self.assertEquals(obj, {
            'success': True,
        })

    @unittest.skipIf(
        settings.FEATURES.get('DISABLE_RESIGN_EMAIL_TEST', False),
        dedent("""
            Skipping Test because CMS has not provided necessary templates for resignation.
            If LMS tests print this message, that needs to be fixed.
        """)
    )
    @patch('django.core.mail.send_mail')
    @patch('student.views.render_to_string', Mock(side_effect=mock_render_to_string, autospec=True))
    def test_resign_email(self, send_email):
        """Tests contents of resign email"""

        good_req = self.request_factory.post('/resign/', {'email': self.user.email})
        good_resp = resign(good_req)
        self.assertEquals(good_resp.status_code, 200)
        obj = json.loads(good_resp.content)
        self.assertEquals(obj, {
            'success': True,
        })

        ((subject, msg, from_addr, to_addrs), sm_kwargs) = send_email.call_args
        #self.assertIn("Resignation from", subject)
        #self.assertIn("You're receiving this e-mail because you requested a resignation", msg)
        self.assertEquals(from_addr, settings.DEFAULT_FROM_EMAIL)
        self.assertEquals(len(to_addrs), 1)
        self.assertIn(self.user.email, to_addrs)

        # test that the user is not active (as well as test_reset_password_email)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)
        url_match = re.search(r'resign_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/', msg).groupdict()
        self.assertEquals(url_match['uidb36'], self.uidb36)
        self.assertEquals(url_match['token'], self.token)

    def test_resign_confirm_with_bad_token(self):
        """Ensures that get request with bad token and uidb36 to /resign_confirm/ is considered invalid link
        """
        bad_req = self.request_factory.get('/resign_confirm/NO-OP/')
        bad_resp = resign_confirm(bad_req, 'NO', 'OP')
        self.assertEquals(bad_resp.status_code, 200)
        self.assertEquals(bad_resp.template_name, 'registration/resign_confirm.html')
        self.assertIsNone(bad_resp.context_data['form'])
        self.assertFalse(bad_resp.context_data['validlink'])

    def test_resign_confirm_with_good_token(self):
        """Ensures that get request with good token and uidb36 to /resign_confirm/ is considered valid link
        """
        good_req = self.request_factory.get('/resign_confirm/{0}-{1}/'.format(self.uidb36, self.token))
        good_resp = resign_confirm(good_req, self.uidb36, self.token)
        self.assertEquals(good_resp.status_code, 200)
        self.assertEquals(good_resp.template_name, 'registration/resign_confirm.html')
        self.assertIsNotNone(good_resp.context_data['form'])
        self.assertTrue(good_resp.context_data['validlink'])

        # assert that the user's UserStanding record is not created yet
        self.assertRaises(
            UserStanding.DoesNotExist,
            UserStanding.objects.get,
            user=self.user)

    @patch('student.views.logout_user')
    def test_resign_confirm_with_good_reason(self, logout_user):
        """Ensures that post request with good resign_reason to /resign_confirm/ makes the user logged out and disabled
        """
        good_req = self.request_factory.post('/resign_confirm/{0}-{1}/'.format(self.uidb36, self.token),
                                             {'resign_reason': self.resign_reason})
        good_resp = resign_confirm(good_req, self.uidb36, self.token)
        self.assertTrue(logout_user.called)

        self.assertEquals(good_resp.status_code, 200)
        self.assertEquals(good_resp.template_name, 'registration/resign_complete.html')
        # assert that the user is active
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)
        # assert that the user's account_status is disabled
        user_account = UserStanding.objects.get(user=self.user)
        self.assertTrue(user_account.account_status, UserStanding.ACCOUNT_DISABLED)
        self.assertTrue(user_account.resign_reason, self.resign_reason)

    def test_resign_confirm_with_empty_reason(self):
        """Ensures that post request with empty resign_reason to /resign_confirm/ is considered invalid form
        """
        bad_req = self.request_factory.post(
            '/resign_confirm/{0}-{1}/'.format(self.uidb36, self.token),
            {'resign_reason': ''}
        )
        bad_resp = resign_confirm(bad_req, self.uidb36, self.token)

        self.assertEquals(bad_resp.status_code, 200)
        self.assertEquals(bad_resp.template_name, 'registration/resign_confirm.html')
        self.assertIsNotNone(bad_resp.context_data['form'])
        # assert that the returned form is invalid
        self.assertFalse(bad_resp.context_data['form'].is_valid())

    def test_resign_confirm_with_over_maxlength_reason(self):
        """Ensures that post request with over maxlength resign_reason to /resign_confirm/ is considered invalid form
        """
        bad_req = self.request_factory.post(
            '/resign_confirm/{0}-{1}/'.format(self.uidb36, self.token),
            {'resign_reason': self.resign_reason + 'a'}
        )
        bad_resp = resign_confirm(bad_req, self.uidb36, self.token)

        self.assertEquals(bad_resp.status_code, 200)
        self.assertEquals(bad_resp.template_name, 'registration/resign_confirm.html')
        self.assertIsNotNone(bad_resp.context_data['form'])
        # assert that the returned form is invalid
        self.assertFalse(bad_resp.context_data['form'].is_valid())
