"""
This file will test through the LMS some of the PasswordHistory features
"""
import json
from mock import patch
from uuid import uuid4
from nose.plugins.attrib import attr

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.test.utils import override_settings

from django.core.urlresolvers import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36

from freezegun import freeze_time

from student.models import PasswordHistory
from courseware.tests.helpers import LoginEnrollmentTestCase


@attr('shard_1')
@patch.dict("django.conf.settings.FEATURES", {'ADVANCED_SECURITY': True})
class TestPasswordHistory(LoginEnrollmentTestCase):
    """
    Go through some of the PasswordHistory use cases
    """

    def _login(self, email, password, should_succeed=True, err_msg_check=None):
        """
        Override the base implementation so we can do appropriate asserts
        """
        resp = self.client.post(reverse('login'), {'email': email, 'password': password})
        data = json.loads(resp.content)

        self.assertEqual(resp.status_code, 200)
        if should_succeed:
            self.assertTrue(data['success'])
        else:
            self.assertFalse(data['success'])
            if err_msg_check:
                self.assertIn(err_msg_check, data['value'])

    def _setup_user(self, is_staff=False, password=None):
        """
        Override the base implementation to randomize the email
        """
        email = 'foo_{0}@test.com'.format(uuid4().hex[:8])
        password = password if password else 'foo'
        username = 'test_{0}'.format(uuid4().hex[:8])
        self.create_account(username, email, password)
        self.activate_user(email)

        # manually twiddle the is_staff bit, if needed
        if is_staff:
            user = User.objects.get(email=email)
            user.is_staff = True
            user.save()

        return email, password

    def _update_password(self, email, new_password):
        """
        Helper method to reset a password
        """
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        history = PasswordHistory()
        history.create(user)

    def assertPasswordResetError(self, response, error_message):
        """
        This method is a custom assertion that verifies that a password reset
        view returns an error response as expected.
        Args:
            response: response from calling a password reset endpoint
            error_message: message we expect to see in the response

        """
        self.assertFalse(response.context_data['validlink'])
        self.assertIn(error_message, response.content)

    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_DAYS_FOR_STAFF_ACCOUNTS_PASSWORD_RESETS': None})
    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_DAYS_FOR_STUDENT_ACCOUNTS_PASSWORD_RESETS': None})
    def test_no_forced_password_change(self):
        """
        Makes sure default behavior is correct when we don't have this turned on
        """

        email, password = self._setup_user()
        self._login(email, password)

        email, password = self._setup_user(is_staff=True)
        self._login(email, password)

    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_DAYS_FOR_STAFF_ACCOUNTS_PASSWORD_RESETS': 1})
    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_DAYS_FOR_STUDENT_ACCOUNTS_PASSWORD_RESETS': 5})
    def test_forced_password_change(self):
        """
        Make sure password are viewed as expired in LMS after the policy time has elapsed
        """

        student_email, student_password = self._setup_user()
        staff_email, staff_password = self._setup_user(is_staff=True)

        self._login(student_email, student_password)
        self._login(staff_email, staff_password)

        staff_reset_time = timezone.now() + timedelta(days=1)
        with freeze_time(staff_reset_time):
            self._login(student_email, student_password)

            # staff should fail because password expired
            self._login(staff_email, staff_password, should_succeed=False,
                        err_msg_check="Your password has expired due to password policy on this account")

            # if we reset the password, we should be able to log in
            self._update_password(staff_email, "updated")
            self._login(staff_email, "updated")

        student_reset_time = timezone.now() + timedelta(days=5)
        with freeze_time(student_reset_time):
            # Both staff and student logins should fail because user must
            # reset the password

            self._login(student_email, student_password, should_succeed=False,
                        err_msg_check="Your password has expired due to password policy on this account")
            self._update_password(student_email, "updated")
            self._login(student_email, "updated")

            self._login(staff_email, staff_password, should_succeed=False,
                        err_msg_check="Your password has expired due to password policy on this account")
            self._update_password(staff_email, "updated2")
            self._login(staff_email, "updated2")

    def test_allow_all_password_reuse(self):
        """
        Tests that password_reset flows work as expected if reuse config is missing, meaning
        passwords can always be reused
        """
        student_email, _ = self._setup_user()
        user = User.objects.get(email=student_email)

        err_msg = 'You are re-using a password that you have used recently.'

        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo'
        }, follow=True)

        self.assertNotIn(
            err_msg,
            resp.content
        )

    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_DIFFERENT_STUDENT_PASSWORDS_BEFORE_REUSE': 1})
    def test_student_password_reset_reuse(self):
        """
        Goes through the password reset flows to make sure the various password reuse policies are enforced
        """
        student_email, _ = self._setup_user()
        user = User.objects.get(email=student_email)

        err_msg = 'You are re-using a password that you have used recently. You must have 1 distinct password'
        success_msg = 'Your Password Reset is Complete'

        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo'
        }, follow=True)

        self.assertPasswordResetError(resp, err_msg)

        # now retry with a different password
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'bar',
            'new_password2': 'bar'
        }, follow=True)

        self.assertIn(success_msg, resp.content)

    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_DIFFERENT_STAFF_PASSWORDS_BEFORE_REUSE': 2})
    def test_staff_password_reset_reuse(self):
        """
        Goes through the password reset flows to make sure the various password reuse policies are enforced
        """
        staff_email, _ = self._setup_user(is_staff=True)
        user = User.objects.get(email=staff_email)

        err_msg = 'You are re-using a password that you have used recently. You must have 2 distinct passwords'
        success_msg = 'Your Password Reset is Complete'

        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo',
        }, follow=True)

        self.assertPasswordResetError(resp, err_msg)

        # now use different one
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'bar',
            'new_password2': 'bar',
        }, follow=True)

        self.assertIn(success_msg, resp.content)

        # now try again with the first one
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo',
        }, follow=True)

        self.assertPasswordResetError(resp, err_msg)

        # now use different one
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'baz',
            'new_password2': 'baz',
        }, follow=True)

        self.assertIn(success_msg, resp.content)

        # now we should be able to reuse the first one
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo',
        }, follow=True)

        self.assertIn(success_msg, resp.content)

    @patch.dict("django.conf.settings.ADVANCED_SECURITY_CONFIG", {'MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS': 1})
    def test_password_reset_frequency_limit(self):
        """
        Asserts the frequency limit on how often we can change passwords
        """
        staff_email, _ = self._setup_user(is_staff=True)

        success_msg = 'Your Password Reset is Complete'

        # try to reset password, it should fail
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo',
        }, follow=True)

        self.assertNotIn(
            success_msg,
            resp.content
        )

        # pretend we're in the future
        staff_reset_time = timezone.now() + timedelta(days=1)
        with freeze_time(staff_reset_time):
            user = User.objects.get(email=staff_email)
            token = default_token_generator.make_token(user)
            uidb36 = int_to_base36(user.id)

            # try to do a password reset with the same password as before
            resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
                'new_password1': 'foo',
                'new_password2': 'foo',
            }, follow=True)

            self.assertIn(success_msg, resp.content)

    @patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': True})
    @override_settings(PASSWORD_MIN_LENGTH=6)
    def test_password_policy_on_password_reset(self):
        """
        This makes sure the proper asserts on password policy also works on password reset
        """
        staff_email, _ = self._setup_user(is_staff=True, password='foofoo')

        success_msg = 'Your Password Reset is Complete'

        # try to reset password, it should fail
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foo',
            'new_password2': 'foo',
        }, follow=True)

        self.assertNotIn(
            success_msg,
            resp.content
        )

        # try to reset password with a long enough password
        user = User.objects.get(email=staff_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': 'foofoo',
            'new_password2': 'foofoo',
        }, follow=True)

        self.assertIn(success_msg, resp.content)
