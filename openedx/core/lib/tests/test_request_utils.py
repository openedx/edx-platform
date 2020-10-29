"""Tests for request_utils module."""


import unittest

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.test.client import RequestFactory

from openedx.core.lib.request_utils import get_request_or_stub, course_id_from_url, safe_get_host


class RequestUtilTestCase(unittest.TestCase):
    """
    Tests for request_utils module.
    """
    def setUp(self):
        super(RequestUtilTestCase, self).setUp()
        self.old_site_name = settings.SITE_NAME
        self.old_allowed_hosts = settings.ALLOWED_HOSTS

    def tearDown(self):
        super(RequestUtilTestCase, self).tearDown()
        settings.SITE_NAME = self.old_site_name
        settings.ALLOWED_HOSTS = self.old_allowed_hosts

    def test_get_request_or_stub(self):
        """
        Outside the context of the request, we should still get a request
        that allows us to build an absolute URI.
        """
        stub = get_request_or_stub()
        expected_url = "http://{site_name}/foobar".format(site_name=settings.SITE_NAME)
        self.assertEqual(stub.build_absolute_uri("foobar"), expected_url)

    def test_safe_get_host(self):
        """ Tests that the safe_get_host function returns the desired host """
        settings.SITE_NAME = 'siteName.com'
        factory = RequestFactory()
        request = factory.request()
        request.META['HTTP_HOST'] = 'www.userProvidedHost.com'
        # If ALLOWED_HOSTS is not set properly, safe_get_host should return SITE_NAME
        settings.ALLOWED_HOSTS = None
        self.assertEqual(safe_get_host(request), "siteName.com")
        settings.ALLOWED_HOSTS = ["*"]
        self.assertEqual(safe_get_host(request), "siteName.com")
        settings.ALLOWED_HOSTS = ["foo.com", "*"]
        self.assertEqual(safe_get_host(request), "siteName.com")

        # If ALLOWED_HOSTS is set properly, and the host is valid, we just return the user-provided host
        settings.ALLOWED_HOSTS = [request.META['HTTP_HOST']]
        self.assertEqual(safe_get_host(request), request.META['HTTP_HOST'])

        # If ALLOWED_HOSTS is set properly but the host is invalid, we should get a SuspiciousOperation
        settings.ALLOWED_HOSTS = ["the_valid_website.com"]
        with self.assertRaises(SuspiciousOperation):
            safe_get_host(request)

    def test_course_id_from_url(self):
        """ Test course_id_from_url(). """

        self.assertIsNone(course_id_from_url('/login'))
        self.assertIsNone(course_id_from_url('/course/edX/maths/2020'))
        self.assertIsNone(course_id_from_url('/courses/edX/maths/'))
        self.assertIsNone(course_id_from_url('/api/courses/v1/blocks/edX/maths/2020'))
        self.assertIsNone(course_id_from_url('/api/courses/v1/blocks/course-v1:incidental+courseid+formatting'))
        self.assertIsNone(course_id_from_url('/api/courses/v41/notcourses/course-v1:incidental+courseid+formatting'))

        course_id = course_id_from_url('/courses/course-v1:edX+maths+2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org="edX", course='maths', run='2020')

        course_id = course_id_from_url('/courses/edX/maths/2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org='edX', course='maths', run='2020')

        course_id = course_id_from_url('/api/courses/v1/courses/course-v1:edX+maths+2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org='edX', course='maths', run='2020')

        course_id = course_id_from_url('/api/courses/v1/courses/edX/maths/2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org='edX', course='maths', run='2020')

    def assertCourseIdFieldsMatch(self, course_id, org, course, run):
        """ Asserts that the passed-in course id matches the specified fields"""
        self.assertEqual(course_id.org, org)
        self.assertEqual(course_id.course, course)
        self.assertEqual(course_id.run, run)
