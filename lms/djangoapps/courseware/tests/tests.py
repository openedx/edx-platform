import json
from django.test import TestCase
from django.test.client import Client
from mock import patch, Mock
from override_settings import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from path import path

from student.models import Registration
from django.contrib.auth.models import User

from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
import copy


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def registration(email):
    '''look up registration object by email'''
    return Registration.objects.get(user__email=email)


TEST_DATA_MODULESTORE = copy.deepcopy(settings.MODULESTORE)
# TODO (vshnayder): test the real courses
TEST_DATA_DIR = 'common/test/data'
TEST_DATA_MODULESTORE['default']['OPTIONS']['fs_root'] = path(TEST_DATA_DIR)

@override_settings(MODULESTORE=TEST_DATA_MODULESTORE)
class IntegrationTestCase(TestCase):
    '''Check that all objects in all accessible courses will load properly'''

    def setUp(self):
        email = 'view@test.com'
        password = 'foo'
        self.create_account('viewtest', email, password)
        self.activate_user(email)
        self.login(email, password)
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()


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

    # ============ Page loading ==============

    def check_pages_load(self, test_course_name):
        import_from_xml(modulestore(), TEST_DATA_DIR, [test_course_name])

        n = 0
        num_bad = 0
        all_ok = True
        for descriptor in modulestore().get_items(
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
            self.assertTrue(all_ok)

        print "{0}/{1} good".format(n - num_bad, n)


    def test_toy_course_loads(self):
        self.check_pages_load('toy')

    def test_full_course_loads(self):
        self.check_pages_load('full')


    # ========= TODO: check ajax interaction here too?
