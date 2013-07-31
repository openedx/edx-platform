'''
Tests for student activation and login
'''
import json
from mock import patch

from django.test import TestCase
from django.test.client import Client
from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from student.tests.factories import UserFactory, RegistrationFactory, UserProfileFactory


class LoginTest(TestCase):
    '''
    Test student.views.login_user() view
    '''

    def setUp(self):
        # Create one user and save it to the database
        self.user = UserFactory.build(username='test', email='test@edx.org')
        self.user.set_password('test_password')
        self.user.save()

        # Create a registration for the user
        RegistrationFactory(user=self.user)

        # Create a profile for the user
        UserProfileFactory(user=self.user)

        # Create the test client
        self.client = Client()
        cache.clear()

        # Store the login url
        try:
            self.url = reverse('login_post')
        except NoReverseMatch:
            self.url = reverse('login')

    def test_login_success(self):
        response, mock_audit_log = self._login_response('test@edx.org', 'test_password', patched_audit_log='student.models.AUDIT_LOG')
        self._assert_response(response, success=True)
        self._assert_audit_log(mock_audit_log, 'info', [u'Login success', u'test@edx.org'])

    def test_login_success_unicode_email(self):
        unicode_email = u'test' + unichr(40960) + u'@edx.org'
        self.user.email = unicode_email
        self.user.save()

        response, mock_audit_log = self._login_response(unicode_email, 'test_password', patched_audit_log='student.models.AUDIT_LOG')
        self._assert_response(response, success=True)
        self._assert_audit_log(mock_audit_log, 'info', [u'Login success', unicode_email])

    def test_login_fail_no_user_exists(self):
        nonexistent_email = u'not_a_user@edx.org'
        response, mock_audit_log = self._login_response(nonexistent_email, 'test_password')
        self._assert_response(response, success=False,
                              value='Email or password is incorrect')
        self._assert_audit_log(mock_audit_log, 'warning', [u'Login failed', u'Unknown user email', nonexistent_email])

    def test_login_fail_wrong_password(self):
        response, mock_audit_log = self._login_response('test@edx.org', 'wrong_password')
        self._assert_response(response, success=False,
                              value='Email or password is incorrect')
        self._assert_audit_log(mock_audit_log, 'warning', [u'Login failed', u'password for', u'test@edx.org', u'invalid'])

    def test_login_not_activated(self):
        # De-activate the user
        self.user.is_active = False
        self.user.save()

        # Should now be unable to login
        response, mock_audit_log = self._login_response('test@edx.org', 'test_password')
        self._assert_response(response, success=False,
                              value="This account has not been activated")
        self._assert_audit_log(mock_audit_log, 'warning', [u'Login failed', u'Account not active for user'])

    def test_login_unicode_email(self):
        unicode_email = u'test@edx.org' + unichr(40960)
        response, mock_audit_log = self._login_response(unicode_email, 'test_password')
        self._assert_response(response, success=False)
        self._assert_audit_log(mock_audit_log, 'warning', [u'Login failed', unicode_email])

    def test_login_unicode_password(self):
        unicode_password = u'test_password' + unichr(1972)
        response, mock_audit_log = self._login_response('test@edx.org', unicode_password)
        self._assert_response(response, success=False)
        self._assert_audit_log(mock_audit_log, 'warning', [u'Login failed', u'password for', u'test@edx.org', u'invalid'])

    def test_logout_logging(self):
        response, _ = self._login_response('test@edx.org', 'test_password')
        self._assert_response(response, success=True)
        logout_url = reverse('logout')
        with patch('student.models.AUDIT_LOG') as mock_audit_log:
            response = self.client.post(logout_url)
        self.assertEqual(response.status_code, 302)
        self._assert_audit_log(mock_audit_log, 'info', [u'Logout', u'test'])

    def test_login_ratelimited_success(self):
        # Try (and fail) logging in with fewer attempts than the limit of 30
        # and verify that you can still successfully log in afterwards.
        for i in xrange(20):
            password = u'test_password{0}'.format(i)
            response, _audit_log = self._login_response('test@edx.org', password)
            self._assert_response(response, success=False)
        # now try logging in with a valid password
        response, _audit_log = self._login_response('test@edx.org', 'test_password')
        self._assert_response(response, success=True)

    def test_login_ratelimited(self):
        # try logging in 30 times, the default limit in the number of failed
        # login attempts in one 5 minute period before the rate gets limited
        for i in xrange(30):
            password = u'test_password{0}'.format(i)
            self._login_response('test@edx.org', password)
        # check to see if this response indicates that this was ratelimited
        response, _audit_log = self._login_response('test@edx.org', 'wrong_password')
        self._assert_response(response, success=False, value='Too many failed login attempts')

    def _login_response(self, email, password, patched_audit_log='student.views.AUDIT_LOG'):
        ''' Post the login info '''
        post_params = {'email': email, 'password': password}
        with patch(patched_audit_log) as mock_audit_log:
            result = self.client.post(self.url, post_params)
        return result, mock_audit_log

    def _assert_response(self, response, success=None, value=None):
        '''
        Assert that the response had status 200 and returned a valid
        JSON-parseable dict.

        If success is provided, assert that the response had that
        value for 'success' in the JSON dict.

        If value is provided, assert that the response contained that
        value for 'value' in the JSON dict.
        '''
        self.assertEqual(response.status_code, 200)

        try:
            response_dict = json.loads(response.content)
        except ValueError:
            self.fail("Could not parse response content as JSON: %s"
                      % str(response.content))

        if success is not None:
            self.assertEqual(response_dict['success'], success)

        if value is not None:
            msg = ("'%s' did not contain '%s'" %
                   (str(response_dict['value']), str(value)))
            self.assertTrue(value in response_dict['value'], msg)

    def _assert_audit_log(self, mock_audit_log, level, log_strings):
        """
        Check that the audit log has received the expected call.
        """
        method_calls = mock_audit_log.method_calls
        self.assertEquals(len(method_calls), 1)
        name, args, _kwargs = method_calls[0]
        self.assertEquals(name, level)
        self.assertEquals(len(args), 1)
        format_string = args[0]
        for log_string in log_strings:
            self.assertIn(log_string, format_string)
