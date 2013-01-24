import logging
from mock import MagicMock, patch
import factory
import copy
from path import path

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.conf import settings
from override_settings import override_settings

from xmodule.modulestore.xml_importer import import_from_xml
import xmodule.modulestore.django

TEST_DATA_MODULESTORE = copy.deepcopy(settings.MODULESTORE)
TEST_DATA_MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')

@override_settings(MODULESTORE=TEST_DATA_MODULESTORE)
class CreateTest(TestCase):
    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        import_from_xml(modulestore(), 'common/test/data/', [test_course_name])

    def check_edit_item(self, test_course_name):
        import_from_xml(modulestore(), 'common/test/data/', [test_course_name])
        for descriptor in modulestore().get_items(Location(None, None, None, None, None)):
            print "Checking ", descriptor.location.url()
            print descriptor.__class__, descriptor.location
            resp = self.client.get(reverse('edit_item'), {'id': descriptor.location.url()})
            self.assertEqual(resp.status_code, 200)

    def test_edit_item_toy(self):
        self.check_edit_item('toy')
    
##    def setUp(self):
##        self.client = Client()
##        self.username = 'username'
##        self.email = 'test@foo.com'
##        self.pw = 'password'
##
##    def create_account(self, username, email, pw):
##        resp = self.client.post('/create_account', {
##            'username': username,
##            'email': email,
##            'password': pw,
##            'location': 'home',
##            'language': 'Franglish',
##            'name': 'Fred Weasley',
##            'terms_of_service': 'true',
##            'honor_code': 'true',
##        })
##        return resp
##
##    def registration(self, email):
##    '''look up registration object by email'''
##        return Registration.objects.get(user__email=email)
##
##    def activate_user(self, email):
##        activation_key = self.registration(email).activation_key
