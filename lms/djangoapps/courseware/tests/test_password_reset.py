"""
This file will test through the LMS some of the password reset features
"""
from uuid import uuid4

import ddt
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.test.utils import override_settings
from django.utils.http import int_to_base36

from courseware.tests.helpers import LoginEnrollmentTestCase
from util.password_policy_validators import create_validator_config


@ddt.ddt
class TestPasswordReset(LoginEnrollmentTestCase):
    """
    Go through some of the password reset use cases
    """
    shard = 1

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

    def assertPasswordResetError(self, response, error_message, valid_link=True):
        """
        This method is a custom assertion that verifies that a password reset
        view returns an error response as expected.
        Args:
            response: response from calling a password reset endpoint
            error_message: message we expect to see in the response
            valid_link: if the current password reset link is still valid

        """
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['validlink'], valid_link)
        self.assertIn(error_message, response.content)

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 6})
    ])
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

    @ddt.data(
        ('foo', 'foobar', 'Error in resetting your password. Please try again.'),
        ('', '', 'This password is too short. It must contain at least'),
    )
    @ddt.unpack
    def test_password_reset_form_invalid(self, password1, password2, err_msg):
        """
        Tests that password reset fail when providing bad passwords and error message is displayed
        to the user.
        """
        user_email, _ = self._setup_user()

        # try to reset password, it should fail
        user = User.objects.get(email=user_email)
        token = default_token_generator.make_token(user)
        uidb36 = int_to_base36(user.id)

        # try to do a password reset with the same password as before
        resp = self.client.post('/password_reset_confirm/{0}-{1}/'.format(uidb36, token), {
            'new_password1': password1,
            'new_password2': password2,
        }, follow=True)
        self.assertPasswordResetError(resp, err_msg)
