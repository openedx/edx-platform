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
from override_settings import override_settings

from xmodule.modulestore.django import modulestore, _MODULESTORES
import contentstore.views as views


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
class ViewsTestCase(TestCase):
    def setUp(self):
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self._MODULESTORES = {}
        self.course_id = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_id)

    def test_has_access(self):
        user = UserFactory()
        user.is_authenticated = True
        set_trace()
        self.assertTrue(views.has_access(user, self.location))
