import copy
import json
from path import path
import os

from pprint import pprint
from nose import SkipTest

from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch, Mock
from override_settings import override_settings

from django.contrib.auth.models import User
from student.models import Registration

from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def registration(email):
    '''look up registration object by email'''
    return Registration.objects.get(user__email=email)


# A bit of a hack--want mongo modulestore for these tests, until
# jump_to works with the xmlmodulestore or we have an even better solution
# NOTE: this means this test requires mongo to be running.

def mongo_store_config(data_dir):
    return {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': {
            'default_class': 'xmodule.raw_module.RawDescriptor',
            'host': 'localhost',
            'db': 'xmodule',
            'collection': 'modulestore',
            'fs_root': data_dir,
        }
    }
}

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_MODULESTORE = mongo_store_config(TEST_DATA_DIR)

REAL_DATA_DIR = settings.GITHUB_REPO_ROOT
REAL_DATA_MODULESTORE = mongo_store_config(REAL_DATA_DIR)

class ActivateLoginTestCase(TestCase):
    '''Check that we can activate and log in'''

    def setUp(self):
        email = 'view@test.com'
        password = 'foo'
        self.create_account('viewtest', email, password)
        self.activate_user(email)
        self.login(email, password)

    # ============ User creation and login ==============

    def _login(self, email, pw):
        '''Login.  View should always return 200.  The success/fail is in the
        returned json'''
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': pw})
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, pw):
        '''Login, check that it worked.'''
        resp = self._login(email, pw)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def _create_account(self, username, email, pw):
        '''Try to create an account.  No error checking'''
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': pw,
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, pw):
        '''Create the account and check that it worked'''
        resp = self._create_account(username, email, pw)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(user(email).is_active)

        return resp

    def _activate_user(self, email):
        '''Look up the activation key for the user, then hit the activate view.
        No error checking'''
        activation_key = registration(email).activation_key

        # and now we try to activate
        resp = self.client.get(reverse('activate', kwargs={'key': activation_key}))
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(user(email).is_active)

    def test_activate_login(self):
        '''The setup function does all the work'''
        pass


class PageLoader(ActivateLoginTestCase):
    ''' Base class that adds a function to load all pages in a modulestore '''

    def check_pages_load(self, course_name, data_dir, modstore):
        print "Checking course {0} in {1}".format(course_name, data_dir)
        import_from_xml(modstore, data_dir, [course_name])

        n = 0
        num_bad = 0
        all_ok = True
        for descriptor in modstore.get_items(
                Location(None, None, None, None, None)):
            n += 1
            print "Checking ", descriptor.location.url()
            #print descriptor.__class__, descriptor.location
            resp = self.client.get(reverse('jump_to',
                                   kwargs={'location': descriptor.location.url()}))
            msg = str(resp.status_code)

            if resp.status_code != 200:
                msg = "ERROR " + msg
                all_ok = False
                num_bad += 1
            print msg
            self.assertTrue(all_ok)  # fail fast

        print "{0}/{1} good".format(n - num_bad, n)
        self.assertTrue(all_ok)


@override_settings(MODULESTORE=TEST_DATA_MODULESTORE)
class TestCoursesLoadTestCase(PageLoader):
    '''Check that all pages in test courses load properly'''

    def setUp(self):
        ActivateLoginTestCase.setUp(self)
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

    def test_toy_course_loads(self):
        self.check_pages_load('toy', TEST_DATA_DIR, modulestore())

    def test_full_course_loads(self):
        self.check_pages_load('full', TEST_DATA_DIR, modulestore())


    # ========= TODO: check ajax interaction here too?


@override_settings(MODULESTORE=REAL_DATA_MODULESTORE)
class RealCoursesLoadTestCase(PageLoader):
    '''Check that all pages in real courses load properly'''

    def setUp(self):
        ActivateLoginTestCase.setUp(self)
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

    def test_real_courses_loads(self):
        '''See if any real courses are available at the REAL_DATA_DIR.
        If they are, check them.'''

        # TODO: Disabled test for now..  Fix once things are cleaned up.
        raise SkipTest
        # TODO: adjust staticfiles_dirs
        if not os.path.isdir(REAL_DATA_DIR):
            # No data present.  Just pass.
            return

        courses = [course_dir for course_dir in os.listdir(REAL_DATA_DIR)
                   if os.path.isdir(REAL_DATA_DIR / course_dir)]
        for course in courses:
            self.check_pages_load(course, REAL_DATA_DIR, modulestore())


    # ========= TODO: check ajax interaction here too?
