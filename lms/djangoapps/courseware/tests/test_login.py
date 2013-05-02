'''
Tests for student activation and login
'''
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from courseware.tests.factories import UserFactory, RegistrationFactory, UserProfileFactory
import json


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

        # Store the login url
        self.url = reverse('login')

    def test_login_success(self):
        response = self._login_response('test@edx.org', 'test_password')
        self._assert_response(response, success=True)

    def test_login_success_unicode_email(self):
        unicode_email = u'test@edx.org' + unichr(40960)

        self.user.email = unicode_email
        self.user.save()

        response = self._login_response(unicode_email, 'test_password')
        self._assert_response(response, success=True)

    def test_login_fail_no_user_exists(self):
        response = self._login_response('not_a_user@edx.org', 'test_password')
        self._assert_response(response, success=False,
                              value='Email or password is incorrect')

    def test_login_fail_wrong_password(self):
        response = self._login_response('test@edx.org', 'wrong_password')
        self._assert_response(response, success=False,
                              value='Email or password is incorrect')

    def test_login_not_activated(self):
        # De-activate the user
        self.user.is_active = False
        self.user.save()

        # Should now be unable to login
        response = self._login_response('test@edx.org', 'test_password')
        self._assert_response(response, success=False,
                              value="This account has not been activated")

    def test_login_unicode_email(self):
        unicode_email = u'test@edx.org' + unichr(40960)
        response = self._login_response(unicode_email, 'test_password')
        self._assert_response(response, success=False)

    def test_login_unicode_password(self):
        unicode_password = u'test_password' + unichr(1972)
        response = self._login_response('test@edx.org', unicode_password)
        self._assert_response(response, success=False)

    def _login_response(self, email, password):
        ''' Post the login info '''
        post_params = {'email': email, 'password': password}
        return self.client.post(self.url, post_params)

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
