import json
import uuid
import unittest
from mock import patch
from datetime import datetime, timedelta
from freezegun import freeze_time
from pytz import UTC

from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.cache import cache
from student.tests.factories import UserFactory

TEST_API_KEY = str(uuid.uuid4())


@override_settings(EDX_API_KEY=TEST_API_KEY)
@patch.dict("django.conf.settings.FEATURES", {'ENABLE_MAX_FAILED_LOGIN_ATTEMPTS': False})

class SessionApiRateLimitingProtectionTest(TestCase):
    """
    Test api_manager.session.login.ratelimit
    """
    def setUp(self):
        """
        Create one user and save it to the database
        """
        self.user = UserFactory.build(username='test', email='test@edx.org')
        self.user.set_password('test_password')
        self.user.save()

        # Create the test client
        self.client = Client()
        cache.clear()
        self.session_url = '/api/sessions'


    def test_login_ratelimiting_protection(self):
        """ Try (and fail) login user 30 times on invalid password """

        for i in xrange(30):
            password = u'test_password{0}'.format(i)
            response = self._do_post_request(self.session_url, 'test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # then the rate limiter should kick in and give a HttpForbidden response
        response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
        message = _('Rate limit exceeded in api login.')
        self._assert_response(response, status=403, message=message)

    def test_login_ratelimiting_unblock(self):
        """ Try (and fail) login user 30 times on invalid password """
        for i in xrange(30):
            password = u'test_password{0}'.format(i)
            response = self._do_post_request(self.session_url, 'test', password, secure=True)
            self.assertEqual(response.status_code, 401)

        # then the rate limiter should kick in and give a HttpForbidden response
        response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
        message = _('Rate limit exceeded in api login.')
        self._assert_response(response, status=403, message=message)

        # now reset the time to 5 mins from now in future in order to unblock
        reset_time = datetime.now(UTC) + timedelta(seconds=300)
        with freeze_time(reset_time):
            response = self._do_post_request(self.session_url, 'test', 'test_password', secure=True)
            self._assert_response(response, status=201)

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
