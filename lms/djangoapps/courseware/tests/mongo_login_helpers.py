import logging
import json

from urlparse import urlsplit, urlunsplit

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import xmodule.modulestore.django

# Need access to internal func to put users in the right group
from courseware import grades
from courseware.model_data import ModelDataCache
from courseware.access import (has_access, _course_staff_group_name,
                               course_beta_test_group_name)

from student.models import Registration
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml import XMLModuleStore

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.mongo import MongoModuleStore
log = logging.getLogger("mitx." + __name__)


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def get_user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def get_registration(email):
    '''look up registration object by email'''
    return Registration.objects.get(user__email=email)


class MongoLoginHelpers(ModuleStoreTestCase):

    def assertRedirectsNoFollow(self, response, expected_url):
        """
        http://devblog.point2.com/2010/04/23/djangos-assertredirects-little-gotcha/

        Don't check that the redirected-to page loads--there should be other tests for that.

        Some of the code taken from django.test.testcases.py
        """
        self.assertEqual(response.status_code, 302,
                         'Response status code was %d instead of 302'
                         % (response.status_code))
        url = response['Location']

        e_scheme, e_netloc, e_path, e_query, e_fragment = urlsplit(expected_url)
        if not (e_scheme or e_netloc):
            expected_url = urlunsplit(('http', 'testserver',
                                       e_path, e_query, e_fragment))

        self.assertEqual(url, expected_url,
                         "Response redirected to '%s', expected '%s'" %
                         (url, expected_url))

    def setup_viewtest_user(self):
        '''create a user account, activate, and log in'''
        self.viewtest_email = 'view@test.com'
        self.viewtest_password = 'foo'
        self.viewtest_username = 'viewtest'
        self.create_account(self.viewtest_username,
                            self.viewtest_email, self.viewtest_password)
        self.activate_user(self.viewtest_email)
        self.login(self.viewtest_email, self.viewtest_password)

    # ============ User creation and login ==============

    def _login(self, email, password):
        '''Login.  View should always return 200.  The success/fail is in the
        returned json'''
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': password})
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, password):
        '''Login, check that it worked.'''
        resp = self._login(email, password)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def logout(self):
        '''Logout, check that it worked.'''
        resp = self.client.get(reverse('logout'), {})
        # should redirect
        self.assertEqual(resp.status_code, 302)
        return resp

    def _create_account(self, username, email, password):
        '''Try to create an account.  No error checking'''
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': password,
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, password):
        '''Create the account and check that it worked'''
        resp = self._create_account(username, email, password)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(get_user(email).is_active)

        return resp

    def _activate_user(self, email):
        '''Look up the activation key for the user, then hit the activate view.
        No error checking'''
        activation_key = get_registration(email).activation_key

        # and now we try to activate
        url = reverse('activate', kwargs={'key': activation_key})
        resp = self.client.get(url)
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(get_user(email).is_active)

    def try_enroll(self, course):
        """Try to enroll.  Return bool success instead of asserting it."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'enroll',
            'course_id': course.id,
        })
        print ('Enrollment in %s result status code: %s'
               % (course.location.url(), str(resp.status_code)))
        return resp.status_code == 200

    def enroll(self, course):
        """Enroll the currently logged-in user, and check that it worked."""
        result = self.try_enroll(course)
        self.assertTrue(result)

    def unenroll(self, course):
        """Unenroll the currently logged-in user, and check that it worked."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'unenroll',
            'course_id': course.id,
        })
        self.assertTrue(resp.status_code == 200)

    def check_for_get_code(self, code, url):
        """
        Check that we got the expected code when accessing url via GET.
        Returns the response.
        """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp

    def check_for_post_code(self, code, url, data={}):
        """
        Check that we got the expected code when accessing url via POST.
        Returns the response.
        """
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp
