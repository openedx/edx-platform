# -*- coding: utf-8 -*-
from django.test import TestCase
from django.http import Http404
from django.test.utils import override_settings
from courseware.courses import get_course_by_id, get_cms_course_link_by_id

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
