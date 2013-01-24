import logging
from mock import MagicMock, patch
import datetime
import factory

from django.test import TestCase
from django.http import Http404, HttpResponse
from django.conf import settings
from django.test.utils import override_settings
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import InvalidLocationError,\
     ItemNotFoundError, NoPathToItem
import courseware.views as views
from xmodule.modulestore import Location
#import mitx.common.djangoapps.mitxmako as mako

class Stub():
    pass

def render_to_response(template_name, dictionary, context_instance=None,
                       namespace='main', **kwargs):
    # The original returns HttpResponse
    print dir()
    print template_name
    print dictionary
    return HttpResponse('foo')

class UserFactory(factory.Factory):
    first_name = 'Test'
    last_name = 'Robot'
    is_staff = True
    is_active = True

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

class ModulestoreTest(TestCase):
    def setUp(self):
        self._MODULESTORES = {}

        # Toy courses should be loaded
        self.course_name = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course('edX/toy/2012_Fall')

    def test(self):
        self.assertEquals(1,2)

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
        # Many functions call upon render_to_response
        # Problem is that we don't know what templates there are?
        views.render_to_response = render_to_response
        #m = mako.MakoMiddleware()

    def test_user_groups(self):
        # depreciated function?
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
        print type(self.toy_course)
        print dir(self.toy_course)
        print self.toy_course.location
        print self.toy_course.__dict__
        valid = ['i4x', 'edX', 'toy', 'chapter', 'overview']
        L = Location('i4x', 'edX', 'toy', 'chapter', 'Overview', None)
        
        views.jump_to(request, 'dummy', L)
        
    def test_static_tab(self):
        mock_request = MagicMock()
        mock_request.user = self.user
        # What is tab_slug?
        #views.static_tab(mock_request, self.course_id, 'dummy')

    def test_university_profile(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_id, chapter)
        request = self.request_factory.get(chapter_url)
        request.user = UserFactory()
        self.assertRaisesRegexp(Http404, 'University Profile*',
                                views.university_profile, request, 'Harvard')
        # Mocked out function render_to_response
        self.assertIsInstance(views.university_profile(request, 'edX'), HttpResponse)

    def test_syllabus(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_id, chapter)
        request = self.request_factory.get(chapter_url)
        request.user = UserFactory()
        # course not found
        views.syllabus(request, self.course_id)

    def test_render_notifications(self):
        request = self.request_factory.get('foo')
        views.render_notifications(request, self.course_id, 'dummy')
