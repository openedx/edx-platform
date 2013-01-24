import unittest
import logging 

from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from override_settings import override_settings

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore, _MODULESTORES
from courseware import views

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
