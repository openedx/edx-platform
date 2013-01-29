import logging
from mock import MagicMock, patch
import json
import factory
import unittest
from nose.tools import set_trace
from nose.plugins.skip import SkipTest

from django.http import Http404, HttpResponse, HttpRequest, HttpResponseRedirect
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
import auth.authz as a
from contentstore.tests.factories import XModuleCourseFactory, CourseFactory


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
        # empty Modulestore
        self._MODULESTORES = {}
        self.course_id = 'edX/toy/2012_Fall'
        self.course_id_2 = 'edx/full/6.002_Spring_2012'
        self.toy_course = modulestore().get_course(self.course_id)

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
        # Instead of raising exception when has_access is False, redirects
        self.assertIsInstance(views.course_index(request, 'edX',
                          'full', '6.002_Spring_2012'), HttpResponseRedirect)
        self.user_2 = MagicMock(is_staff = True, is_active = True)
        self.user_2.is_authenticated.return_value = True
        request_2 = MagicMock(user = self.user_2)
        # Bug? Raises error because calls modulestore().get_item(location)
        #NotImplementedError: XMLModuleStores can't guarantee that definitions
        #are unique. Use get_instance.
        print views.course_index(request_2, 'edX',
                          'full', '6.002_Spring_2012')

    def test_edit_subsection(self):
        self.user = MagicMock(is_staff = False, is_active = False)
        self.user.is_authenticated.return_value = False
        self.request = MagicMock(user = self.user)
        self.assertIsInstance(views.edit_subscription(self.request, self.location_2),
                              HttpResponseRedirect)
        
