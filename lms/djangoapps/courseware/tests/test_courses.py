# -*- coding: utf-8 -*-
from django.test import TestCase
from django.http import Http404
from courseware.courses import get_course_by_id, get_cms_course_link_by_id

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

    def test_get_cms_course_link_by_id(self):
        """
        Tests that get_cms_course_link_by_id returns the right thing
        """
        self.assertEqual("//localhost:8001/", get_cms_course_link_by_id("blah_bad_course_id"))
        self.assertEqual("//localhost:8001/", get_cms_course_link_by_id("too/too/many/slashes"))
        self.assertEqual("//localhost:8001/org/num/course/name", get_cms_course_link_by_id('org/num/name'))