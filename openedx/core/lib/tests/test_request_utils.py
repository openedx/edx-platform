"""Tests for request_utils module."""


import unittest
from unittest.mock import Mock, patch, call

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.test.client import RequestFactory

from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.lib.request_utils import (
    get_request_or_stub,
    course_id_from_url,
    safe_get_host,
    CookieMonitoringMiddleware,
    CAPTURE_COOKIE_SIZES,
)


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

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        mock_request = Mock()
        mock_request.COOKIES = {
            "a": "." * 100,
            "_b": "." * 13,
            "_c_": "." * 13,
            "a.b": "." * 10,
            "a.c": "." * 10,
            "b.": "." * 13,
            "b_a": "." * 15,
            "b_c": "." * 15,
        }

        middleware.process_request(mock_request)

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.a.size', 100),
            call('cookies._b.size', 13),
            call('cookies._c_.size', 13),
            call('cookies.a.b.size', 10),
            call('cookies.a.c.size', 10),
            call('cookies.b..size', 13),
            call('cookies.b_a.size', 15),
            call('cookies.b_c.size', 15),
            call('cookies.a.group.size', 20),
            call('cookies.b.group.size', 43),
            call('cookies.max.name', 'a'),
            call('cookies.max.size', 100),
            # Test that single cookie is also treated as a group for max calculations.
            call('cookies.max.group.name', 'a'),
            call('cookies.max.group.size', 100),
            call('cookies_total_size', 189)
        ])

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring_max_group(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        mock_request = Mock()
        mock_request.COOKIES = {
            "a": "." * 10,
            "b_a": "." * 15,
            "b_c": "." * 20,
        }

        middleware.process_request(mock_request)

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.a.size', 10),
            call('cookies.b_a.size', 15),
            call('cookies.b_c.size', 20),
            call('cookies.b.group.size', 35),
            call('cookies.max.name', 'b_c'),
            call('cookies.max.size', 20),
            call('cookies.max.group.name', 'b'),
            call('cookies.max.group.size', 35),
            call('cookies_total_size', 45)
        ])
