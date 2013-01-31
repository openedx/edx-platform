import logging
from mock import MagicMock, patch
import json
import factory
import unittest
from nose.tools import set_trace
from nose.plugins.skip import SkipTest
from collections import defaultdict

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
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorModule
from contentstore.utils import get_course_for_item

class Stub():
    pass

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
        #modulestore().collection.drop()
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self.location_2 = ['i4x', 'edX', 'full', 'course', '6.002_Spring_2012']
        self.location_3 = ['i4x', 'MITx', '999', 'course', 'Robot_Super_Course']
        # empty Modulestore
        self._MODULESTORES = {}
        self.course_id = 'edX/toy/2012_Fall'
        self.course_id_2 = 'edx/full/6.002_Spring_2012'
        # is a CourseDescriptor object?
        self.course = CourseFactory.create()
        # is a sequence descriptor
        self.item = ItemFactory.create(template = 'i4x://edx/templates/sequential/Empty')

    def tearDown(self):
        _MODULESTORES = {}
        modulestore().collection.drop()
        #assert False
        
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

    def test_load_preview_state(self):
        # Tests that function creates empty defaultdict when request.session
        # is empty
        # location cannot be a list or other mutable type
        self.request = RequestFactory().get('foo')
        self.request.session = {}
        instance_state, shared_state = views.load_preview_state(self.request,
                                                        'foo', 'bar')
        self.assertIsNone(instance_state)
        self.assertIsNone(shared_state)

    def test_save_preview_state(self):
        self.request = RequestFactory().get('foo')
        self.request.session = {}
        loc = Location(self.location_3)
        result = {'preview_states':
                                      {('id', loc):{'instance':None,
                                                        'shared':None,
                                                        }
                                        }
                }
        views.save_preview_state(self.request, 'id', loc, None, None)
        self.assertEquals(self.request.session, result)

    def test_get_preview_module(self):
        raise SkipTest
        self.request = RequestFactory().get('foo')
        self.request.user = UserFactory()
        mock_descriptor = MagicMock()
        mock_descriptor.get_sample_state.return_value = [('foo','bar')]
        instance, shared = views.get_preview_module(self.request, 'id', mock_descriptor)
        self.assertEquals(instance, 'foo')

    def test_preview_module_system(self):
        # Returns a ModuleSystem
        self.request = RequestFactory().get('foo')
        self.request.user = UserFactory()
        self.assertIsInstance(views.preview_module_system(self.request,
                                                          'id', self.course),
                              ModuleSystem)

    def test_load_preview_module(self):
         
        self.request = RequestFactory().get('foo')
        self.request.user = UserFactory()
        self.request.session = {}
        self.assertIsInstance(views.load_preview_module(self.request, 'id',
                                        self.course, 'instance', 'shared'),
                              ErrorModule)
        system = views.preview_module_system(self.request, 'id', self.course)
        # is a functools.partial object?
        # Not sure how to get a valid line 507
        print self.course.xmodule_constructor(system)
        print self.course.xmodule_constructor(system).func
        print self.course.xmodule_constructor(system).keywords
        print dir(self.course.xmodule_constructor(system).func)

    def test__xmodule_recurse(self):
        #There shouldn't be a difference, but the code works with defined
        # function f but not with lambda functions
        mock_item = MagicMock()
        mock_item.get_children.return_value = []
        s = Stub()
        s.children.append(Stub())
        views._xmodule_recurse(s, f)
        self.assertEquals(s.n, 1)
        self.assertEquals(s.children[0].n, 1)

    def test_get_module_previews(self):
        # needs a working render_to_string
        raise SkipTest
        self.request = RequestFactory().get('foo')
        self.request.user = UserFactory()
        self.request.session = {}
        print views.get_module_previews(self.request, self.course)

    def test_delete_item(self):
        # If user doesn't have permission, redirect
        self.no_permit_user = MagicMock(is_staff = False, is_active = False)
        self.no_permit_user.is_authenticated.return_value = True
        self.request = RequestFactory().post('i4x://MITx/999/course/Robot_Super_Course')
        self.request.POST = self.request.POST.copy()
        self.request.POST.update({'id':'i4x://MITx/999/course/Robot_Super_Course'})
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.delete_item, self.request)
        # Should return an HttpResponse
        self.permit_user =MagicMock(is_staff = True, is_active = True)
        self.permit_user.is_authenticated.return_value = True
        self.request_2 = RequestFactory().post(self.item.location.url())
        self.request_2.POST = self.request_2.POST.copy()
        self.request_2.POST.update({'id':self.item.location.url()})
        self.request_2.user = self.permit_user
        response = views.delete_item(self.request_2)
        self.assertIsInstance(response, HttpResponse)
        self.assertEquals(modulestore().get_items(self.item.location.url()), [])
        # Set delete_children to True to delete all children
        # Create children
        self.item_2 = ItemFactory.create()
        child_item = ItemFactory.create()
##        print type(self.item_2)
##        print self.item_2.__dict__
        # Is there better way of adding children? What format are children in?
        self.item_2.definition['children'] = [child_item.location.url()]
        self.request_3 = RequestFactory().post(self.item_2.location.url())
        self.request_3.POST = self.request_3.POST.copy()
        self.request_3.POST.update({'id':self.item_2.location.url(),
                                    'delete_children':True,
                                    'delete_all_versions':True})
        self.request_3.user = self.permit_user
        print self.item_2.get_children()
        self.assertIsInstance(views.delete_item(self.request_3), HttpResponse)
        self.assertEquals(modulestore().get_items(self.item_2.location.url()), [])
        # Problem: Function doesn't delete child item?
        # child_item can be manually deleted, but can't delete it using function
        # Not sure if problem with _xmodule_recurse and lambda functions
        #store = views.get_modulestore(child_item.location.url())
        #store.delete_item(child_item.location)
        self.assertEquals(modulestore().get_items(child_item.location.url()), [])
        # Check delete_item on 'vertical'
        self.item_3 = ItemFactory.create(template = 'i4x://edx/templates/vertical/Empty')
        self.request_4 = RequestFactory().post(self.item_3.location.url())
        self.request_4.POST = self.request_4.POST.copy()
        self.request_4.POST.update({'id':self.item_3.location.url(),
                                    'delete_children':True,
                                    'delete_all_versions':True})
        self.request_4.user = self.permit_user
        self.assertIsInstance(views.delete_item(self.request_4), HttpResponse)
        self.assertEquals(modulestore().get_items(self.item_3.location.url()), [])
    
    def test_save_item(self):
        # Test that user with no permissions gets redirected
        self.no_permit_user = MagicMock(is_staff = False, is_active = False)
        self.no_permit_user.is_authenticated.return_value = True
        self.request = RequestFactory().post(self.item.location.url())
        self.request.POST = self.request.POST.copy()
        self.request.POST.update({'id':self.item.location.url()})
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.save_item, self.request)
        # Test user with permissions but nothing in request.POST
        self.item_2 = ItemFactory.create()
        self.permit_user =MagicMock(is_staff = True, is_active = True)
        self.permit_user.is_authenticated.return_value = True
        self.request_2 = RequestFactory().post(self.item_2.location.url())
        self.request_2.POST = self.request.POST.copy()
        self.request_2.POST.update({'id':self.item_2.location.url()})
        self.request_2.user = self.permit_user
        self.assertIsInstance(views.save_item(self.request_2), HttpResponse)
        # Test updating data
        self.request_3 = RequestFactory().post(self.item_2.location.url())
        self.request_3.POST = self.request.POST.copy()
        self.request_3.POST.update({'id':self.item_2.location.url(),
                                    'data':{'foo':'bar'}})
        self.request_3.user = self.permit_user
        self.assertIsInstance(views.save_item(self.request_3), HttpResponse)
        self.assertEquals(modulestore().get_item(self.item_2.location.dict()).definition['data'],
                          {u'foo': u'bar'})
        # Test metadata, which is a dictionary?
        self.request_4 = RequestFactory().post(self.item_2.location.url())
        self.request_4.POST = self.request.POST.copy()
        self.request_4.POST.update({'id':self.item_2.location.url(),
                                    'metadata':{'foo':'bar'}})
        self.request_4.user = self.permit_user
        self.assertIsInstance(views.save_item(self.request_4), HttpResponse)
        self.assertEquals(modulestore().get_item(self.item_2.location.dict()).metadata['foo'],
                          'bar')
        

def f(x):
    x.n += 1
    
class Stub():
    def __init__(self):
        self.n = 0
        self.children = []
    def get_children(self):
        return self.children
    
