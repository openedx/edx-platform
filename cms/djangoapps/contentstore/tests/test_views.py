import logging
from mock import MagicMock, patch
import json
import factory
import unittest
from nose.tools import set_trace
from nose.plugins.skip import SkipTest

from django.http import Http404, HttpResponse, HttpRequest, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from override_settings import override_settings
from django.core.exceptions import PermissionDenied

from xmodule.modulestore.django import modulestore, _MODULESTORES
import contentstore.views as views
from contentstore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore import Location


def xml_store_config(data_dir):
    return {
    'default': {
        'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
        'OPTIONS': {
            'data_dir': data_dir,
            'default_class': 'xmodule.hidden_module.HiddenDescriptor',
        }
    }
}

class UserFactory(factory.Factory):
    first_name = 'Test'
    last_name = 'Robot'
    is_staff = True
    is_active = True

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)

class ViewsTestCase(TestCase):
    def setUp(self):
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self.location_2 = ['i4x', 'edX', 'full', 'course', '6.002_Spring_2012']
        self.location_3 = ['i4x', 'MITx', '999', 'course', 'Robot_Super_Course']
        # empty Modulestore
        self._MODULESTORES = {}
        self.course_id = 'edX/toy/2012_Fall'
        self.course_id_2 = 'edx/full/6.002_Spring_2012'
        #self.toy_course = modulestore().get_course(self.course_id)
        # Problem: Classes persist, need to delete stuff from modulestore
        # is a CourseDescriptor object?
        self.course = CourseFactory.create()
        # is a sequence descriptor
        self.item = ItemFactory.create(template = 'i4x://edx/templates/sequential/Empty')

    def tearDown(self):
        _MODULESTORES = {}
        modulestore().collection.drop()
        
    def test_has_access(self):
        user = MagicMock(is_staff = True, is_active = True, is_authenticated = True)
        m = MagicMock()
        m.count.return_value = 1
        user.groups.filter.return_value = m
        self.assertTrue(views.has_access(user, self.location_2))
        user.is_authenticated = False
        self.assertFalse(views.has_access(user, self.location_2))

    def test_course_index(self):
        # UserFactory doesn't work?
        self.user = MagicMock(is_staff = False, is_active = False)
        self.user.is_authenticated.return_value = False
        request = MagicMock(user = self.user)
        # Redirects if request.user doesn't have access to location
        self.assertIsInstance(views.course_index(request, 'edX',
                          'full', '6.002_Spring_2012'), HttpResponseRedirect)
        self.user_2 = MagicMock(is_staff = True, is_active = True)
        self.user_2.is_authenticated.return_value = True
        request_2 = MagicMock(user = self.user_2)
        # Doesn't work unless we figure out render_to_response
##        views.course_index(request_2, 'MITx',
##                          '999', 'Robot_Super_Course')

    def test_edit_subsection(self):
        # Redirects if request.user doesn't have access to location
        self.user = MagicMock(is_staff = False, is_active = False)
        self.user.is_authenticated.return_value = False
        self.request = MagicMock(user = self.user)
        self.assertIsInstance(views.edit_subsection(self.request, self.location_2),
                              HttpResponseRedirect)
        # If location isn't for a "sequential", return Bad Request
        self.user_2 = MagicMock(is_staff = True, is_active = True)
        self.user_2.is_authenticated.return_value = True
        self.request_2 = MagicMock(user = self.user_2)
        self.assertIsInstance(views.edit_subsection(self.request_2,
                                        self.location_3), HttpResponseBadRequest)
        # Need render_to_response
        #views.edit_subsection(self.request_2, self.item.location)
    
    def test_edit_unit(self):
        # if user doesn't have access, should redirect
        self.user = MagicMock(is_staff = False, is_active = False)
        self.user.is_authenticated.return_value = False
        self.request = MagicMock(user = self.user)
        self.assertIsInstance(views.edit_unit(self.request, self.location_2),
                              HttpResponseRedirect)

    def test_assignment_type_update(self):
        # If user doesn't have access, should redirect
        self.user = MagicMock(is_staff = False, is_active = False)
        self.user.is_authenticated.return_value = False
        self.request = RequestFactory().get('foo')
        self.request.user = self.user
        self.assertIsInstance(views.assignment_type_update(self.request,
                                    'MITx', '999', 'course', 'Robot_Super_Course'),
                              HttpResponseRedirect)
        # if user has access, then should return HttpResponse
        self.user_2 = MagicMock(is_staff = True, is_active = True)
        self.user_2.is_authenticated.return_value = True
        self.request.user = self.user_2
        get_response = views.assignment_type_update(self.request,'MITx', '999',
                                                    'course', 'Robot_Super_Course')
        self.assertIsInstance(get_response,HttpResponse)
        get_response_string = '{"id": 99, "location": ["i4x", "MITx", "999", "course", "Robot_Super_Course", null], "graderType": "Not Graded"}'
        self.assertEquals(get_response.content, get_response_string)
        self.request_2 = RequestFactory().post('foo')
        self.request_2.user = self.user_2
        post_response = views.assignment_type_update(self.request_2,'MITx', '999',
                                                    'course', 'Robot_Super_Course')
        self.assertIsInstance(post_response,HttpResponse)
        self.assertEquals(post_response.content, 'null')
