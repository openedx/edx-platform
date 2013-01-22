import unittest
import logging 

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from override_settings import override_settings

import factory
from django.contrib.auth.models import User

from xmodule.modulestore.django import modulestore, _MODULESTORES
from courseware import module_render

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

class UserFactory(factory.Factory):
    first_name = 'Test'
    last_name = 'Robot'
    is_staff = True
    is_active = True

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

        actual = module_render.toc_for_course(self.portal_user, request, self.toy_course, chapter, None)
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

        actual = module_render.toc_for_course(self.portal_user, request, self.toy_course, chapter, section)
        self.assertEqual(expected, actual)