import logging
from mock import MagicMock, patch
import datetime
import factory
import unittest
import os
from nose.plugins.skip import SkipTest

from django.test import TestCase
from django.http import Http404, HttpResponse
from django.conf import settings
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore, _MODULESTORES
from xmodule.modulestore.exceptions import InvalidLocationError,\
     ItemNotFoundError, NoPathToItem
import courseware.views as views
from xmodule.modulestore import Location

def skipped(func):
    from nose.plugins.skip import SkipTest
    def _():
        raise SkipTest("Test %s is skipped" % func.__name__)
    _.__name__ = func.__name__
    return _

#from override_settings import override_settings

class Stub():
    pass

##def render_to_response(template_name, dictionary, context_instance=None,
##                       namespace='main', **kwargs):
##    # The original returns HttpResponse
##    print dir()
##    print template_name
##    print dictionary
##    return HttpResponse('foo')

class UserFactory(factory.Factory):
    first_name = 'Test'
    last_name = 'Robot'
    is_staff = True
    is_active = True

def skipped(func):
    from nose.plugins.skip import SkipTest
    def _():
        raise SkipTest("Test %s is skipped" % func.__name__)
    _.__name__ = func.__name__
    return _

# This part is required for modulestore() to work properly
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


#class ModulestoreTest(TestCase):

@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestJumpTo(TestCase):
    """Check the jumpto link for a course"""
    def setUp(self):
        self._MODULESTORES = {}

        # Toy courses should be loaded
        self.course_name = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course('edX/toy/2012_Fall')

    def test_jumpto_invalid_location(self):
        location = Location('i4x', 'edX', 'toy', 'NoSuchPlace', None)
        jumpto_url = '%s/%s/jump_to/%s' % ('/courses', self.course_name, location)
        expected = 'courses/edX/toy/2012_Fall/courseware/Overview/'
        response = self.client.get(jumpto_url)
        self.assertEqual(response.status_code, 404)

    def test_jumpto_from_chapter(self):
        location = Location('i4x', 'edX', 'toy', 'chapter', 'Overview')
        jumpto_url = '%s/%s/jump_to/%s' % ('/courses', self.course_name, location)
        expected = 'courses/edX/toy/2012_Fall/courseware/Overview/'
        response = self.client.get(jumpto_url)
        self.assertRedirects(response, expected, status_code=302, target_status_code=302)

class ViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='dummy', password='123456',
                                        email='test@mit.edu')
        self.date = datetime.datetime(2013,1,22)
        self.course_id = 'edx/toy/2012_Fall'
        self.enrollment = CourseEnrollment.objects.get_or_create(user = self.user,
                                                  course_id = self.course_id,
                                                  created = self.date)[0]
        self.location = ['tag', 'org', 'course', 'category', 'name']
        self._MODULESTORES = {}
        # This is a CourseDescriptor object
        self.toy_course = modulestore().get_course('edX/toy/2012_Fall')
        self.request_factory = RequestFactory()

    def test_user_groups(self):
        # depreciated function
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertEquals(views.user_groups(mock_user),[])
        

    @override_settings(DEBUG = True)
    def test_user_groups_debug(self):
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = True
        pass
        #views.user_groups(mock_user)
        #Keep going later

    def test_get_current_child(self):
        self.assertIsNone(views.get_current_child(Stub()))
        mock_xmodule = MagicMock()
        mock_xmodule.position = -1
        mock_xmodule.get_display_items.return_value = ['one','two']
        self.assertEquals(views.get_current_child(mock_xmodule), 'one')
        mock_xmodule_2 = MagicMock()
        mock_xmodule_2.position = 3
        mock_xmodule_2.get_display_items.return_value = []
        self.assertIsNone(views.get_current_child(mock_xmodule_2))

    def test_redirect_to_course_position(self):
        mock_module = MagicMock()
        mock_module.descriptor.id = 'Underwater Basketweaving'
        mock_module.position = 3
        mock_module.get_display_items.return_value = []
        self.assertRaises(Http404, views.redirect_to_course_position,
                          mock_module, True)

    def test_index(self):
        pass
        #print modulestore()
        #assert False

    def test_registered_for_course(self):
        self.assertFalse(views.registered_for_course('Basketweaving', None))
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertFalse(views.registered_for_course('dummy', mock_user))
        mock_course = MagicMock()
        mock_course.id = self.course_id
        self.assertTrue(views.registered_for_course(mock_course, self.user))

    def test_jump_to(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_id, chapter)
        request = self.request_factory.get(chapter_url)
        self.assertRaisesRegexp(Http404, 'Invalid location', views.jump_to,
                                request, 'bar', ())
        self.assertRaisesRegexp(Http404, 'No data*', views.jump_to, request,
                                'dummy', self.location)
##        print type(self.toy_course)
##        print dir(self.toy_course)
##        print self.toy_course.location
##        print self.toy_course.__dict__
##        valid = ['i4x', 'edX', 'toy', 'chapter', 'overview']
##        L = Location('i4x', 'edX', 'toy', 'chapter', 'Overview', None)
##        
##        views.jump_to(request, 'dummy', L)
        
    def test_static_tab(self):
        request = self.request_factory.get('foo')
        request.user = self.user
        self.assertRaises(Http404, views.static_tab, request, 'edX/toy/2012_Fall',
                          'dummy')
        # What are valid tab_slugs?
##        request_2 = self.request_factory.get('foo')
##        request_2.user = UserFactory()
        
    def test_static_university_profile(self):
        # TODO
        # Can't test unless have a valid template file
        raise SkipTest
        request = self.client.get('university_profile/edX')
        self.assertIsInstance(views.static_university_profile(request, 'edX'), HttpResponse)
        
    def test_university_profile(self):
        raise SkipTest
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_id, chapter)
        request = self.request_factory.get(chapter_url)
        request.user = UserFactory()
        self.assertRaisesRegexp(Http404, 'University Profile*',
                                views.university_profile, request, 'Harvard')
        # TODO
        #request_2 = self.client.get('/university_profile/edx')
        self.assertIsInstance(views.university_profile(request, 'edX'), HttpResponse)
        # Can't continue testing unless have valid template file

    
    def test_syllabus(self):
        raise SkipTest
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_id, chapter)
        request = self.request_factory.get(chapter_url)
        request.user = UserFactory()
        # Can't find valid template
        # TODO
        views.syllabus(request, 'edX/toy/2012_Fall')

    def test_render_notifications(self):
        request = self.request_factory.get('foo')
        #views.render_notifications(request, self.course_id, 'dummy')
        # TODO
        # Needs valid template

    def test_news(self):
        raise SkipTest
        # Bug? get_notifications is actually in lms/lib/comment_client/legacy.py
        request = self.client.get('/news')
        self.user.id = 'foo'
        request.user = self.user
        course_id = 'edX/toy/2012_Fall'
        self.assertIsInstance(views.news(request, course_id), HttpResponse)
        
        # TODO
