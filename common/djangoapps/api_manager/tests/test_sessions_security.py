"""
Tests for session api with advance security features
"""
import json
import uuid
import unittest

from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.cache import cache
from student.tests.factories import UserFactory

TEST_API_KEY = str(uuid.uuid4())

@override_settings(EDX_API_KEY=TEST_API_KEY, ENABLE_MAX_FAILED_LOGIN_ATTEMPTS=True)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class SessionApiSecurityTest(TestCase):
    """
    Test api_manager.session.session_list view
    """

    def setUp(self):
        # Create one user and save it to the database
        self.user = UserFactory.build(username='test', email='test@edx.org')
        self.user.set_password('test_password')
        self.user.save()

        # Create the test client
        self.client = Client()
        cache.clear()
        self.url = '/api/sessions/'

    @override_settings(MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED=10)
    def test_login_ratelimited_success(self):
        # Try (and fail) logging in with fewer attempts than the limit of 10
        # and verify that you can still successfully log in afterwards.
        for i in xrange(9):
            password = u'test_password{0}'.format(i)
            response = self._login_response('test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # now try logging in with a valid password and check status
        response = self._login_response('test', 'test_password', secure=True)
        self._assert_response(response, status=201)

    @override_settings(MAX_FAILED_LOGIN_ATTEMPTS_ALLOWED=10)
    def test_login_blockout(self):
        # Try (and fail) logging in with 10 attempts
        # and verify that user is blocked out.
        for i in xrange(10):
            password = u'test_password{0}'.format(i)
            response = self._login_response('test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # check to see if this response indicates blockout
        response = self._login_response('test', 'test_password', secure=True)
        message = _('This account has been temporarily locked due to excessive login failures. Try again later.')
        self._assert_response(response, status=403, message=message)

    def _login_response(self, username, password, secure=False):
        """
        Post the login info
        """
        post_params, extra = {'username': username, 'password': password}, {}
        headers = {'X-Edx-Api-Key': TEST_API_KEY, 'Content-Type': 'application/json'}
        if secure:
            extra['wsgi.url_scheme'] = 'https'
        return self.client.post(self.url, post_params, headers=headers, **extra)

    def _assert_response(self, response, status=200, success=None, message=None):
        """
        Assert that the response had status 200 and returned a valid
        JSON-parseable dict.

        If success is provided, assert that the response had that
        value for 'success' in the JSON dict.

        If message is provided, assert that the response contained that
        value for 'message' in the JSON dict.
        """
        self.assertEqual(response.status_code, status)

        try:
            response_dict = json.loads(response.content)
        except ValueError:
            self.fail("Could not parse response content as JSON: %s"
                      % str(response.content))

        if success is not None:
            self.assertEqual(response_dict['success'], success)

        if message is not None:
            msg = ("'%s' did not contain '%s'" %
                   (response_dict['message'], message))
            self.assertTrue(message in response_dict['message'], msg)
