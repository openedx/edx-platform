# -*- coding: utf-8 -*-
"""
Tests for course access
"""
import datetime
from mock import MagicMock
import mock

from django.test import TestCase
from django.conf import settings
from django.http import Http404
from django.contrib.auth.models import User
from django.test.client import RequestFactory

from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

import courseware.views as views
from django.test.utils import override_settings
from courseware.courses import get_course_by_id, get_course, get_cms_course_link_by_id
from xmodule.modulestore.django import get_default_store_name_for_current_request

CMS_BASE_TEST = 'testcms'


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


class CoursesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='dummy', password='123456',
                                        email='test@mit.edu')
        self.date = datetime.datetime(2013, 1, 22, tzinfo=UTC)
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

    def test_registered_for_course(self):
        self.assertFalse(views.registered_for_course('Basketweaving', None))
        mock_user = MagicMock()
        mock_user.is_authenticated.return_value = False
        self.assertFalse(views.registered_for_course('dummy', mock_user))
        mock_course = MagicMock()
        mock_course.id = self.course_id
        self.assertTrue(views.registered_for_course(mock_course, self.user))

=======
>>>>>>> origin/release
class CoursesTest(TestCase):
    """Test methods related to fetching courses."""

    def test_get_course_by_id_invalid_chars(self):
        """
        Test that `get_course_by_id` throws a 404, rather than
        an exception, when faced with unexpected characters
        (such as unicode characters, and symbols such as = and ' ')
        """
        with self.assertRaises(Http404):
            get_course_by_id('MITx/foobar/statistics=introduction')
            get_course_by_id('MITx/foobar/business and management')
            get_course_by_id('MITx/foobar/NiñøJoséMaríáßç')

    def test_get_course_invalid_chars(self):
        """
        Test that `get_course` throws a ValueError, rather than
        a 404, when faced with unexpected characters
        (such as unicode characters, and symbols such as = and ' ')
        """
        with self.assertRaises(ValueError):
            get_course('MITx/foobar/statistics=introduction')
            get_course('MITx/foobar/business and management')
            get_course('MITx/foobar/NiñøJoséMaríáßç')

    @override_settings(CMS_BASE=CMS_BASE_TEST)
    def test_get_cms_course_link_by_id(self):
        """
        Tests that get_cms_course_link_by_id returns the right thing
        """
        self.assertEqual("//{}/".format(CMS_BASE_TEST), get_cms_course_link_by_id("blah_bad_course_id"))
        self.assertEqual("//{}/".format(CMS_BASE_TEST), get_cms_course_link_by_id("too/too/many/slashes"))
        self.assertEqual("//{}/org/num/course/name".format(CMS_BASE_TEST), get_cms_course_link_by_id('org/num/name'))

    @mock.patch('xmodule.modulestore.django.get_current_request_hostname', mock.Mock(return_value='preview.localhost'))
    @override_settings(HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': 'draft'})
    def test_default_modulestore_preview_mapping(self):
        self.assertEqual(get_default_store_name_for_current_request(), 'draft')

    @mock.patch('xmodule.modulestore.django.get_current_request_hostname', mock.Mock(return_value='localhost'))
    @override_settings(HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={r'preview\.': 'draft'})
    def test_default_modulestore_published_mapping(self):
        self.assertEqual(get_default_store_name_for_current_request(), 'default')
