import logging
from mock import MagicMock, patch
import datetime
import factory
import unittest
import os

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

from .factories import UserFactory


class Stub():
    pass


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
        self.date = datetime.datetime(2013, 1, 22)
        self.course_id = 'edX/toy/2012_Fall'
        self.enrollment = CourseEnrollment.objects.get_or_create(user=self.user,
                                                  course_id=self.course_id,
                                                  created=self.date)[0]
        self.location = ['tag', 'org', 'course', 'category', 'name']
        self._MODULESTORES = {}
        # This is a CourseDescriptor object
        self.toy_course = modulestore().get_course('edX/toy/2012_Fall')
        self.request_factory = RequestFactory()
        chapter = 'Overview'
        self.chapter_url = '%s/%s/%s' % ('/courses', self.course_id, chapter)

    def test_user_groups(self):
        # depreciated function
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertEquals(views.user_groups(mock_user), [])

    def test_get_current_child(self):
        self.assertIsNone(views.get_current_child(Stub()))
        mock_xmodule = MagicMock()
        mock_xmodule.position = -1
        mock_xmodule.get_display_items.return_value = ['one', 'two']
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
                          mock_module)

    def test_registered_for_course(self):
        self.assertFalse(views.registered_for_course('Basketweaving', None))
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertFalse(views.registered_for_course('dummy', mock_user))
        mock_course = MagicMock()
        mock_course.id = self.course_id
        self.assertTrue(views.registered_for_course(mock_course, self.user))

    def test_jump_to_invalid(self):
        request = self.request_factory.get(self.chapter_url)
        self.assertRaisesRegexp(Http404, 'Invalid location', views.jump_to,
                                request, 'bar', ())
        self.assertRaisesRegexp(Http404, 'No data*', views.jump_to, request,
                                'dummy', self.location)
