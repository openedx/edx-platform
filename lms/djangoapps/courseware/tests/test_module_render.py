import logging
from mock import MagicMock, patch
import json
import factory
import unittest
from nose.tools import set_trace
from nose.plugins.skip import SkipTest

from django.http import Http404, HttpResponse, HttpRequest
from django.conf import settings
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse 

from courseware.models import StudentModule, StudentModuleCache 
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.exceptions import NotFoundError 
from xmodule.modulestore import Location
import courseware.module_render as render
from override_settings import override_settings
from xmodule.modulestore.django import modulestore, _MODULESTORES
from xmodule.seq_module import SequenceModule
from courseware.tests.tests import PageLoader
from student.models import Registration 

class Stub:
    def __init__(self):
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

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class ModuleRenderTestCase(PageLoader):
    def setUp(self):
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self._MODULESTORES = {}
        self.course_id = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_id)

    def test_toc_for_course(self):
        mock_course = MagicMock()
        mock_course.id = 'dummy'
        mock_course.location = Location(self.location)
        mock_course.get_children.return_value = []
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertIsNone(render.toc_for_course(mock_user,'dummy',
                                                mock_course, 'dummy', 'dummy'))
        # rest of tests are in class TestTOC

    def test_get_module(self):
        self.assertIsNone(render.get_module('dummyuser',None,\
                                            'invalid location',None,None))
        #done

    def test__get_module(self):
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        location = Location('i4x', 'edX', 'toy', 'chapter', 'Overview')
        mock_request = MagicMock()
        s = render._get_module(mock_user, mock_request, location,
                                'dummy', 'edX/toy/2012_Fall')
        self.assertIsInstance(s, SequenceModule)
        # Don't know how to generate error in line 260 to test
        # Can't tell if sequence module is an error?

    def test_get_instance_module(self):
        # done
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertIsNone(render.get_instance_module('dummy', mock_user, 'dummy',
                                                     'dummy'))
        mock_user_2 = MagicMock()
        mock_user_2.is_authenticated.return_value = True
        mock_module = MagicMock()
        mock_module.descriptor.stores_state = False
        self.assertIsNone(render.get_instance_module('dummy', mock_user_2,
                                                     mock_module,'dummy'))

    def test_get_shared_instance_module(self):
        raise SkipTest
        mock_user = MagicMock(User)
        mock_user.is_authenticated.return_value = False
        self.assertIsNone(render.get_shared_instance_module('dummy', mock_user, 'dummy',
                     'dummy'))
        mock_user_2 = MagicMock(User)
        mock_user_2.is_authenticated.return_value = True
        
        mock_module = MagicMock(shared_state_key = 'key')
        mock_module.location = Location('i4x', 'edX', 'toy', 'chapter', 'Overview')
        mock_module.get_shared_state.return_value = '{}'
        mock_cache = MagicMock()
        mock_cache.lookup.return_value = False
        #mock_cache._state = 'dummy'
        #set_trace()
        print mock_module.get_shared_state()
        s = render.get_shared_instance_module(self.course_id, mock_user_2,
                                              mock_module, mock_cache)
        self.assertIsInstance(s, StudentModule)
        # Problem: can't get code to take branch that creates StudentModule?
        # Can't finish testing modx_dispatch

    def test_xqueue_callback(self):
        mock_request = MagicMock()
        mock_request.POST.copy.return_value = {}
        # 339
        self.assertRaises(Http404, render.xqueue_callback,mock_request,
                          'dummy', 'dummy', 'dummy', 'dummy')
        mock_request_2 = MagicMock()
        xpackage = {'xqueue_header': json.dumps({}), 
        'xqueue_body'  : 'Message from grader'}
        mock_request_2.POST.copy.return_value = xpackage
        # 342
        self.assertRaises(Http404, render.xqueue_callback,mock_request_2,
                          'dummy', 'dummy', 'dummy', 'dummy')
        mock_request_3 = MagicMock()
        xpackage_2 = {'xqueue_header': json.dumps({'lms_key':'secretkey'}), 
        'xqueue_body'  : 'Message from grader'}
        mock_request_3.POST.copy.return_value = xpackage_2
        # Roadblock: how to get user registered in class?
        raise SkipTest
        #
        # trying alternate way of creating account in hopes of getting valid id
        # Problem: Can't activate user
        
        self.student_name = '12'
        self.password = 'foo'
        self.email = 'test@mit.edu'
        self.create_account(self.student_name, self.email, self.password)
        self.activate_user(self.email)
        request = RequestFactory().get('stuff')
        # This doesn't work to install user
        render.xqueue_callback(mock_request_3, self.course_id,
                               self.student_name, self.password, 'dummy')

    def test_modx_dispatch(self):
        self.assertRaises(Http404, render.modx_dispatch, 'dummy', 'dummy',
                          'invalid Location', 'dummy')
        mock_request = MagicMock()
        mock_request.FILES.keys.return_value = ['file_id']
        mock_request.FILES.getlist.return_value = ['file']*(settings.MAX_FILEUPLOADS_PER_INPUT + 1)
        self.assertEquals(render.modx_dispatch(mock_request, 'dummy', self.location,
                                          'dummy').content,
                         json.dumps({'success': 'Submission aborted! Maximum %d files may be submitted at once' %\
                                     settings.MAX_FILEUPLOADS_PER_INPUT}))
        mock_request_2 = MagicMock()
        mock_request_2.FILES.keys.return_value = ['file_id']
        inputfile = Stub()
        inputfile.size = 1 + settings.STUDENT_FILEUPLOAD_MAX_SIZE
        inputfile.name = 'name'
        filelist = [inputfile]
        mock_request_2.FILES.getlist.return_value = filelist
        self.assertEquals(render.modx_dispatch(mock_request_2, 'dummy', self.location,
                                               'dummy').content,
                          json.dumps({'success': 'Submission aborted! Your file "%s" is too large (max size: %d MB)' %\
                                        (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE/(1000**2))}))
        mock_request_3 = MagicMock()
        mock_request_3.POST.copy.return_value = {}
        mock_request_3.FILES = False
        mock_request_3.user = UserFactory()
        inputfile_2 = Stub()
        inputfile_2.size = 1
        inputfile_2.name = 'name'
        self.assertRaises(ItemNotFoundError, render.modx_dispatch,
                          mock_request_3, 'dummy', self.location, 'toy')
        self.assertRaises(Http404,render.modx_dispatch, mock_request_3, 'dummy',
                            self.location, self.course_id)
##        student_module_cache = StudentModuleCache.cache_for_descriptor_descendents(self.course_id, 
##                mock_request_3.user, modulestore().get_instance(self.course_id, self.location))
##        get_shared_instance_module(course_id, request.user, instance, student_module_cache)
        # 'goto_position' is the only dispatch that will work
        mock_request_3.POST.copy.return_value = {'position':1}
        self.assertIsInstance(render.modx_dispatch(mock_request_3, 'goto_position',
                            self.location, self.course_id), HttpResponse)
        # keep going
        
    def test_preview_chemcalc(self):
        mock_request = MagicMock(method = 'notGET')
        self.assertRaises(Http404, render.preview_chemcalc, mock_request)
        mock_request_2 = MagicMock(method = 'GET')
        mock_request_2.GET.get.return_value = None
        self.assertEquals(render.preview_chemcalc(mock_request_2).content,
                          json.dumps({'preview':'',
                                      'error':'No formula specified.'}))

        mock_request_3 = MagicMock()
        mock_request_3.method = 'GET'
        # Test fails because chemcalc.render_to_html always parses strings?
        mock_request_3.GET.get.return_value = unicode('\x12400', errors="strict")
##        self.assertEquals(render.preview_chemcalc(mock_request_3).content,
##                          json.dumps({'preview':'',
##                                      'error':"Couldn't parse formula: formula"}))
##        
        mock_request_3 = MagicMock()
        mock_request_3.method = 'GET'
        mock_request_3.GET.get.return_value = Stub()
        self.assertEquals(render.preview_chemcalc(mock_request_3).content,
                          json.dumps({'preview':'',
                                      'error':"Error while rendering preview"}))
        

    def test_get_score_bucket(self):
        self.assertEquals(render.get_score_bucket(0, 10), 'incorrect')
        self.assertEquals(render.get_score_bucket(1, 10), 'partial')
        self.assertEquals(render.get_score_bucket(10, 10), 'correct')
        # get_score_bucket calls error cases 'incorrect'
        self.assertEquals(render.get_score_bucket(11, 10), 'incorrect')
        self.assertEquals(render.get_score_bucket(-1, 10), 'incorrect')

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestTOC(TestCase):
    """Check the Table of Contents for a course"""
    def setUp(self):
        self._MODULESTORES = {}

        # Toy courses should be loaded
        self.course_name = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_name)
        self.portal_user = UserFactory()

    def test_toc_toy_from_chapter(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_name, chapter)
        factory = RequestFactory()
        request = factory.get(chapter_url)

        expected = ([{'active': True, 'sections': 
                    [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True, 
                    'format': u'Lecture Sequence', 'due': '', 'active': False}, 
                    {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True, 
                    'format': '', 'due': '', 'active': False}, 
                    {'url_name': 'video_123456789012', 'display_name': 'video 123456789012', 'graded': True, 
                    'format': '', 'due': '', 'active': False}, 
                    {'url_name': 'video_4f66f493ac8f', 'display_name': 'video 4f66f493ac8f', 'graded': True, 
                    'format': '', 'due': '', 'active': False}], 
                    'url_name': 'Overview', 'display_name': u'Overview'}, 
                    {'active': False, 'sections': 
                    [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True, 
                    'format': '', 'due': '', 'active': False}], 
                    'url_name': 'secret:magic', 'display_name': 'secret:magic'}])

        actual = render.toc_for_course(self.portal_user, request, self.toy_course, chapter, None)
        self.assertEqual(expected, actual)

    def test_toc_toy_from_section(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_name, chapter)
        section = 'Welcome'
        factory = RequestFactory()
        request = factory.get(chapter_url)

        expected = ([{'active': True, 'sections': 
                    [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True, 
                    'format': u'Lecture Sequence', 'due': '', 'active': False}, 
                    {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True, 
                    'format': '', 'due': '', 'active': True}, 
                    {'url_name': 'video_123456789012', 'display_name': 'video 123456789012', 'graded': True, 
                    'format': '', 'due': '', 'active': False}, 
                    {'url_name': 'video_4f66f493ac8f', 'display_name': 'video 4f66f493ac8f', 'graded': True, 
                    'format': '', 'due': '', 'active': False}], 
                    'url_name': 'Overview', 'display_name': u'Overview'}, 
                    {'active': False, 'sections': 
                    [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True, 
                    'format': '', 'due': '', 'active': False}], 
                    'url_name': 'secret:magic', 'display_name': 'secret:magic'}])

        actual = render.toc_for_course(self.portal_user, request, self.toy_course, chapter, section)
        self.assertEqual(expected, actual)

