# -*- coding: utf-8 -*-
import mock

from django.test import TestCase
from django.http import Http404
from django.test.utils import override_settings
from courseware.courses import get_course_by_id, get_cms_course_link_by_id
from xmodule.modulestore.django import get_default_store_name_for_current_request

CMS_BASE_TEST = 'testcms'

class CoursesTest(TestCase):
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

    @override_settings(CMS_BASE=CMS_BASE_TEST)
    def test_get_cms_course_link_by_id(self):
        """
        Tests that get_cms_course_link_by_id returns the right thing
        """
        self.assertEqual("//{}/".format(CMS_BASE_TEST), get_cms_course_link_by_id("blah_bad_course_id"))
        self.assertEqual("//{}/".format(CMS_BASE_TEST), get_cms_course_link_by_id("too/too/many/slashes"))
        self.assertEqual("//{}/org/num/course/name".format(CMS_BASE_TEST), get_cms_course_link_by_id('org/num/name'))


    @mock.patch('xmodule.modulestore.django.get_current_request_hostname', mock.Mock(return_value='preview.localhost'))
    @override_settings(HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={'preview\.': 'draft'})
    def test_default_modulestore_preview_mapping(self):   
        self.assertEqual(get_default_store_name_for_current_request(), 'draft')

    @mock.patch('xmodule.modulestore.django.get_current_request_hostname', mock.Mock(return_value='localhost'))
    @override_settings(HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS={'preview\.': 'draft'})
    def test_default_modulestore_published_mapping(self):
        self.assertEqual(get_default_store_name_for_current_request(), 'default')
