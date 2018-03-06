"""
Tests for student deletion
"""
import json

from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseBadRequest, HttpResponse
from mock import patch
import unittest

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from student.tests.factories import UserFactory, RegistrationFactory, UserProfileFactory
from openedx.core.djangoapps.user_api.accounts.api import delete_user_account


@unittest.skipUnless(settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'), 'third party auth not enabled')
class UserDeleteTest(CacheIsolationTestCase):
    """
    Test student account deletion api
    """

    ENABLED_CACHES = ['default']

    def setUp(self):
        super(UserDeleteTest, self).setUp()
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

    def _login_response(self, email, password, patched_audit_log='student.views.AUDIT_LOG', extra_post_params=None):
        ''' Post the login info '''
        post_params = {'email': email, 'password': password}
        if extra_post_params is not None:
            post_params.update(extra_post_params)
        with patch(patched_audit_log) as mock_audit_log:
            result = self.client.post(self.url, post_params)
        return result, mock_audit_log

    def test_delete_success(self):
        '''
        Test if a user is deleted and all values are after creation
        '''
        login_response, mock_audit_log = self._login_response('test@edx.org', 'test_password', patched_audit_log='student.models.AUDIT_LOG')
        login_response = json.loads(login_response.content)
        if login_response['success']:
            try:
                response = delete_user_account(self.user.id)
                self.assertEqual(response, True)
            except Exception, e:
                self.fail("Could not delete and anonymise user : %s" % str(e))
        else:
            self.fail("Could not login to created user")
