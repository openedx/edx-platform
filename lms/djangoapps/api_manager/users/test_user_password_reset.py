"""
Tests for session api with advance security features
"""
import json
import uuid
from mock import patch
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.core.cache import cache
from datetime import datetime, timedelta
from freezegun import freeze_time
from pytz import UTC

TEST_API_KEY = str(uuid.uuid4())


@override_settings(EDX_API_KEY=TEST_API_KEY)
@patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': True})
@patch.dict("django.conf.settings.FEATURES", {'ADVANCED_SECURITY': True})
@override_settings(PASSWORD_MIN_LENGTH=4, PASSWORD_MAX_LENGTH=12,
                   PASSWORD_COMPLEXITY={'UPPER': 2, 'LOWER': 2, 'PUNCTUATION': 2, 'DIGITS': 2})
class UserPasswordResetTest(TestCase):
    """
    Test api_manager.session.session_list view
    """

    def setUp(self):
        """
        setup the api urls
        """
        self.session_url = '/api/sessions'
        self.user_url = '/api/users'
        cache.clear()

    @override_settings(ADVANCED_SECURITY_CONFIG={'MIN_DAYS_FOR_STUDENT_ACCOUNTS_PASSWORD_RESETS': 5})
    def test_user_must_reset_password_after_n_days(self):
        """
            Test to ensure that User session login fails
            after N days. User must reset his/her
            password after N days to login again
        """
        response = self._do_post_request(
            self.user_url, 'test2', 'Test.Me64!', email='test@edx.org',
            first_name='John', last_name='Doe', secure=True
        )
        self._assert_response(response, status=201)
        user_id = response.data['id']

        response = self._do_post_request(self.session_url, 'test2', 'Test.Me64!', secure=True)
        self.assertEqual(response.status_code, 201)

        reset_time = timezone.now() + timedelta(days=5)
        with patch.object(timezone, 'now', return_value=reset_time):
            response = self._do_post_request(self.session_url, 'test2', 'Test.Me64!', secure=True)
            message = _(
                'Your password has expired due to password policy on this account. '
                'You must reset your password before you can log in again.'
            )
            self._assert_response(response, status=403, message=message)

            #reset the password and then try login
            pass_reset_url = "%s/%s" % (self.user_url, str(user_id))
            response = self._do_post_pass_reset_request(
                pass_reset_url, password='Test.Me64@', secure=True
            )
            self.assertEqual(response.status_code, 200)

            #login successful after reset password
            response = self._do_post_request(self.session_url, 'test2', 'Test.Me64@', secure=True)
            self.assertEqual(response.status_code, 201)

    @override_settings(ADVANCED_SECURITY_CONFIG={'MIN_DIFFERENT_STUDENT_PASSWORDS_BEFORE_REUSE': 4,
                                                 'MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS': 0})
    def test_password_reset_not_allowable_reuse(self):
        """
        Try resetting user password  < 4 and > 4 times and
        then use one of the passwords that you have used
        before
        """
        response = self._do_post_request(
            self.user_url, 'test2', 'Test.Me64!', email='test@edx.org',
            first_name='John', last_name='Doe', secure=True
        )
        self._assert_response(response, status=201)
        user_id = response.data['id']

        pass_reset_url = "%s/%s" % (self.user_url, str(user_id))
        response = self._do_post_pass_reset_request(
            pass_reset_url, password='Test.Me64#', secure=True
        )
        self._assert_response(response, status=200)

        response = self._do_post_pass_reset_request(
            pass_reset_url, password='Test.Me64@', secure=True
        )
        self._assert_response(response, status=200)

        response = self._do_post_pass_reset_request(
            pass_reset_url, password='Test.Me64^', secure=True
        )
        self._assert_response(response, status=200)

        #now use previously used password
        response = self._do_post_pass_reset_request(
            pass_reset_url, password='Test.Me64!', secure=True
        )
        message = _(
            "You are re-using a password that you have used recently. You must "
            "have 4 distinct password(s) before reusing a previous password."
        )
        self._assert_response(response, status=403, message=message)

        response = self._do_post_pass_reset_request(
            pass_reset_url, password='Test.Me64&', secure=True
        )
        self._assert_response(response, status=200)

        #now use previously used password
        response = self._do_post_pass_reset_request(
            pass_reset_url, password='Test.Me64!', secure=True
        )
        self._assert_response(response, status=200)

    @override_settings(ADVANCED_SECURITY_CONFIG={'MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS': 1})
    def test_is_password_reset_too_frequent(self):
        """
        Try reset user password before
        and after the MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS
        """
        response = self._do_post_request(
            self.user_url, 'test2', 'Test.Me64!', email='test@edx.org',
            first_name='John', last_name='Doe', secure=True
        )
        self._assert_response(response, status=201)
        user_id = response.data['id']

        pass_reset_url = "%s/%s" % (self.user_url, str(user_id))
        response = self._do_post_pass_reset_request(
            pass_reset_url, password='NewP@ses34!', secure=True
        )
        message = _(
            "You are resetting passwords too frequently. Due to security policies, "
            "1 day(s) must elapse between password resets"
        )
        self._assert_response(response, status=403, message=message)

        reset_time = timezone.now() + timedelta(days=1)
        with patch.object(timezone, 'now', return_value=reset_time):
            response = self._do_post_pass_reset_request(
                pass_reset_url, password='NewP@ses34!', secure=True
            )
            self._assert_response(response, status=200)

    @override_settings(ADVANCED_SECURITY_CONFIG={'MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS': 0})
    def test_password_reset_rate_limiting_unblock(self):
        """
        Try (and fail) login user 30 times on invalid password
        and then unblock it after 5 minutes
         """
        response = self._do_post_request(
            self.user_url, 'test2', 'Test.Me64!', email='test@edx.org',
            first_name='John', last_name='Doe', secure=True
        )
        self._assert_response(response, status=201)
        user_id = response.data['id']

        pass_reset_url = '{}/{}'.format(self.user_url, user_id)

        for i in xrange(30):
            password = u'test_password{0}'.format(i)
            response = self._do_post_pass_reset_request(
                '{}/{}'.format(self.user_url, i + 200),
                password=password,
                secure=True
            )
            self._assert_response(response, status=404)

        response = self._do_post_pass_reset_request(
            '{}/{}'.format(self.user_url, '31'), password='Test.Me64@', secure=True
        )
        message = _('Rate limit exceeded in password_reset.')
        self._assert_response(response, status=403, message=message)

        # now reset the time to 5 mins from now in future in order to unblock
        reset_time = datetime.now(UTC) + timedelta(seconds=300)
        with freeze_time(reset_time):
            response = self._do_post_pass_reset_request(
                pass_reset_url, password='Test.Me64@', secure=True
            )
            self._assert_response(response, status=200)

    def _do_post_request(self, url, username, password, **kwargs):
        """
        Post the login info
        """
        post_params, extra = {'username': username, 'password': password}, {}
        if kwargs.get('email'):
            post_params['email'] = kwargs.get('email')
        if kwargs.get('first_name'):
            post_params['first_name'] = kwargs.get('first_name')
        if kwargs.get('last_name'):
            post_params['last_name'] = kwargs.get('last_name')

        headers = {'X-Edx-Api-Key': TEST_API_KEY, 'Content-Type': 'application/json'}
        if kwargs.get('secure', False):
            extra['wsgi.url_scheme'] = 'https'
        return self.client.post(url, post_params, headers=headers, **extra)

    def _do_post_pass_reset_request(self, url, password, **kwargs):
        """
        Post the Password Reset info
        """
        post_params, extra = {'password': password}, {}

        headers = {'X-Edx-Api-Key': TEST_API_KEY, 'Content-Type': 'application/json'}
        if kwargs.get('secure', False):
            extra['wsgi.url_scheme'] = 'https'
        return self.client.post(url, post_params, headers=headers, **extra)

    def _assert_response(self, response, status=200, message=None):
        """
        Assert that the response had status 200 and returned a valid
        JSON-parseable dict.

        If message is provided, assert that the response contained that
        value for 'message' in the JSON dict.
        """
        self.assertEqual(response.status_code, status)
        response_dict = json.loads(response.content)

        if message is not None:
            msg = ("'%s' did not contain '%s'" %
                   (response_dict['message'], message))
            self.assertTrue(message in response_dict['message'], msg)
