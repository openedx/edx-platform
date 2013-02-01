import logging
from mock import MagicMock, patch
import json
import factory
import unittest
from nose.tools import set_trace
from nose.plugins.skip import SkipTest
from collections import defaultdict
import re

from django.http import (Http404, HttpResponse, HttpRequest,
                         HttpResponseRedirect, HttpResponseBadRequest,
                         HttpResponseForbidden)
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import Client, RequestFactory
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from override_settings import override_settings
from django.core.exceptions import PermissionDenied

from xmodule.modulestore.django import modulestore, _MODULESTORES
from xmodule.modulestore import Location
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorModule
from xmodule.seq_module import SequenceModule
from xmodule.templates import update_templates
from contentstore.utils import get_course_for_item
from contentstore.tests.factories import UserFactory
from contentstore.tests.factories import CourseFactory, ItemFactory
import contentstore.views as views
from contentstore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore import Location
from xmodule.x_module import ModuleSystem
from xmodule.error_module import ErrorModule
from contentstore.utils import get_course_for_item
from xmodule.templates import update_templates

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

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)

class ViewsTestCase(TestCase):
    def setUp(self):
        # empty Modulestore
        self._MODULESTORES = {}
        modulestore().collection.drop()
        update_templates()
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self.location_2 = ['i4x', 'edX', 'full', 'course', '6.002_Spring_2012']
        self.location_3 = ['i4x', 'MITx', '999', 'course', 'Robot_Super_Course']
        self.course_id = 'edX/toy/2012_Fall'
        self.course_id_2 = 'edx/full/6.002_Spring_2012'
        # is a CourseDescriptor object?
        self.course = CourseFactory.create()
        # is a sequence descriptor
        self.item = ItemFactory.create(template = 'i4x://edx/templates/sequential/Empty')
        self.no_permit_user = UserFactory()
        self.permit_user = UserFactory(is_staff = True, username = 'Wizardly Herbert')

    def tearDown(self):
        _MODULESTORES = {}
        modulestore().collection.drop()
        
    def test_has_access(self):
        self.assertTrue(views.has_access(self.permit_user, self.location_2))
        self.assertFalse(views.has_access(self.no_permit_user, self.location_2))
        # done

    def test_course_index(self):
        request = RequestFactory().get('foo')
        request.user = self.no_permit_user
        # Redirects if request.user doesn't have access to location
        self.assertRaises(PermissionDenied, views.course_index, request, 'edX',
                          'full', '6.002_Spring_2012')
        request_2 = RequestFactory().get('foo')
        request.user = self.permit_user
        
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
        self.request = RequestFactory().get('foo')
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.edit_subsection, self.request,
                          self.location_2)
        # If location isn't for a "sequential", return Bad Request
        self.request_2 = RequestFactory().get('foo')
        self.request_2.user = self.permit_user
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
        raise SkipTest
        # if user doesn't have access, should redirect
        self.request = RequestFactory().get('foo')
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.edit_unit, self.request,
                          self.location_2)
        self.request_2 = RequestFactory().get('foo')
        self.request_2.user = self.permit_user
        # Problem: no parent locations, so IndexError
        #print modulestore().get_parent_locations(self.location_3, None)
        views.edit_unit(self.request_2, self.location_3)
        # Needs render_to_response

    def test_assignment_type_update(self):
        raise SkipTest
        # If user doesn't have access, should return HttpResponseForbidden()
        self.request = RequestFactory().get('foo')
        self.request.user = self.no_permit_user
        self.assertIsInstance(views.assignment_type_update(self.request,
                                    'MITx', '999', 'course', 'Robot_Super_Course'),
                              HttpResponseForbidden)
##        views.assignment_type_update(self.request, 'MITx', '999', 'course', 'Robot_Super_Course')
        # if user has access, then should return HttpResponse
        self.request.user = self.permit_user
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
        self.request_2.user = self.permit_user
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
        # Done

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
        # Done

    def test_get_preview_module(self):
        self.request = RequestFactory().get('foo')
        self.request.user = self.permit_user
        self.request.session = {}
        module = views.get_preview_module(self.request, 'id', self.course)
        self.assertIsInstance(module, SequenceModule)
        # Done

    def test_preview_module_system(self):
        # Returns a ModuleSystem
        self.request = RequestFactory().get('foo')
        self.request.user = self.no_permit_user
        self.assertIsInstance(views.preview_module_system(self.request,
                                                          'id', self.course),
                              ModuleSystem)
        # done

    def test_load_preview_module(self):
        # if error in getting module, return ErrorModule
        self.request = RequestFactory().get('foo')
        self.request.user = self.no_permit_user
        self.assertIsInstance(views.preview_module_system(self.request,
                                                          'id', self.course),
                              ModuleSystem)
        self.request.session = {}
        self.assertIsInstance(views.load_preview_module(self.request, 'id',
                                        self.course, 'instance', 'shared'),
                              ErrorModule)
        instance_state, shared_state = self.course.get_sample_state()[0]
        module = views.load_preview_module(self.request,'id', self.course,
                                           instance_state, shared_state)
        self.assertIsInstance(module, SequenceModule)
        # I'd like to test module.get_html, but it relies on render_to_string
        # Test static_tab
        self.course_2 = CourseFactory(display_name = 'Intro_to_intros', location = Location('i4x', 'MITx', '666', 'static_tab', 'Intro_to_intros'))
        module_2 = views.load_preview_module(self.request,'id', self.course_2,
                                             instance_state, shared_state)
        self.assertIsInstance(module, SequenceModule)
        # needs render_to_string

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
        raise SkipTest
        # needs a working render_to_string
        self.request = RequestFactory().get('foo')
        self.request.user = UserFactory()
        self.request.session = {}
        print views.get_module_previews(self.request, self.course)

    def test_delete_item(self):
        raise SkipTest
        # If user doesn't have permission, redirect
        self.request = RequestFactory().post('i4x://MITx/999/course/Robot_Super_Course')
        self.request.POST = self.request.POST.copy()
        self.request.POST.update({'id':'i4x://MITx/999/course/Robot_Super_Course'})
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.delete_item, self.request)
        # Should return an HttpResponse
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
        self.request = RequestFactory().post(self.item.location.url())
        self.request.POST = self.request.POST.copy()
        self.request.POST.update({'id':self.item.location.url()})
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.save_item, self.request)
        # Test user with permissions but nothing in request.POST
        self.item_2 = ItemFactory.create()
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
        # Test updating metadata
        self.request_4 = RequestFactory().post(self.item_2.location.url())
        self.request_4.POST = self.request.POST.copy()
        self.request_4.POST.update({'id':self.item_2.location.url(),
                                    'metadata':{'foo':'bar'}})
        self.request_4.user = self.permit_user
        self.assertIsInstance(views.save_item(self.request_4), HttpResponse)
        self.assertEquals(modulestore().get_item(self.item_2.location.dict()).metadata['foo'],
                          'bar')
        #done

    def test_clone_item(self):
        # Test that user with no permissions gets redirected
        self.request = RequestFactory().post(self.item.location.url())
        self.request.POST = self.request.POST.copy()
        self.request.POST.update({'id':self.item.location.url(),
                                  'parent_location':self.course.location.url(),
                                  'template':self.location_3,
                                  'display_name':'bar'})
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.clone_item, self.request)
        self.request.user = self.permit_user
        response = views.clone_item(self.request)
        self.assertIsInstance(response, HttpResponse)
        self.assertRegexpMatches(response.content, '{"id": "i4x://MITx/999/course/')
        # Done

    def test_upload_asset(self):
        # Test get request
        self.request = RequestFactory().get('foo')
        self.assertIsInstance(views.upload_asset(self.request,'org', 'course',
                                                 'coursename'), HttpResponseBadRequest)
        # Test no permissions
        self.request_2 = RequestFactory().post('foo')
        self.request_2.user = self.no_permit_user
        self.assertIsInstance(views.upload_asset(self.request_2, 'MITx', '999',
                                    'Robot_Super_Course'), HttpResponseForbidden)
        # Test if course exists
        
        self.request_3 = RequestFactory().post('foo')
        self.request_3.user = self.permit_user
        # Throws error because of improperly formatted log
##        self.assertIsInstance(views.upload_asset(self.request_3,'org', 'course',
##                                                 'coursename'),HttpResponseBadRequest)
        # Test response with fake file attached
        # Not sure how to create fake file for testing purposes because
        # can't override request.FILES
##        print self.request_3.FILES
##        print type(self.request_3.FILES)
##        f = open('file.txt')
##        self.request_4 = RequestFactory().post('foo', f)
##        print self.request_3.FILES
##        mock_file = MagicMock(name = 'Secrets', content_type = 'foo')
##        mock_file.read.return_value = 'stuff'
##        file_dict = {'file':mock_file}
##        self.request_3.FILES = file_dict
##        print views.upload_asset(self.request_3, 'MITx', '999',
##                                    'Robot_Super_Course')

    def test_manage_users(self):
        self.request = RequestFactory().get('foo')
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.manage_users, self.request,
                          self.location_3)
        # Needs render_to_response

    def test_create_json_response(self):
        ok_response = views.create_json_response()
        self.assertIsInstance(ok_response, HttpResponse)
        self.assertEquals(ok_response.content, '{"Status": "OK"}')
        bad_response = views.create_json_response('Spacetime collapsing')
        self.assertIsInstance(bad_response, HttpResponse)
        self.assertEquals(bad_response.content, '{"Status": "Failed", "ErrMsg": "Spacetime collapsing"}')

    def test_reorder_static_tabs(self):
        self.request = RequestFactory().get('foo')
        self.request.POST = {'tabs':[self.location_3]}
        self.request.user = self.no_permit_user
        self.assertRaises(PermissionDenied, views.reorder_static_tabs, self.request)
        self.request.user = self.permit_user
        self.assertIsInstance(views.reorder_static_tabs(self.request),
                              HttpResponseBadRequest)
        # to be continued ...

def f(x):
    x.n += 1
    
class Stub():
    def __init__(self):
        self.n = 0
        self.children = []
    def get_children(self):
        return self.children
    
