"""Tests for request_utils module."""

import ddt
import unittest
from unittest.mock import Mock, patch, call

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.http import HttpResponseForbidden
from django.test.client import RequestFactory
from django.test.utils import override_settings
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied


from openedx.core.lib.request_utils import (
    get_request_or_stub,
    course_id_from_url,
    safe_get_host,
    CookieMonitoringMiddleware,
    Monitor403Middleware,
)


class RequestUtilTestCase(unittest.TestCase):
    """
    Tests for request_utils module.
    """
    def setUp(self):
        super(RequestUtilTestCase, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
        self.old_site_name = settings.SITE_NAME
        self.old_allowed_hosts = settings.ALLOWED_HOSTS

    def tearDown(self):
        super(RequestUtilTestCase, self).tearDown()  # lint-amnesty, pylint: disable=super-with-arguments
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
            call('cookies.1.name', 'a'),
            call('cookies.1.size', 100),
            call('cookies.2.name', 'b_a'),
            call('cookies.2.size', 15),
            call('cookies.3.name', 'b_c'),
            call('cookies.3.size', 15),
            call('cookies.4.name', '_b'),
            call('cookies.4.size', 13),
            call('cookies.5.name', '_c_'),
            call('cookies.5.size', 13),
            call('cookies.group.1.name', 'b'),
            call('cookies.group.1.size', 43),
            call('cookies.group.2.name', 'a'),
            call('cookies.group.2.size', 20),
            call('cookies.max.name', 'a'),
            call('cookies.max.size', 100),
            call('cookies.max.group.name', 'a'),
            call('cookies.max.group.size', 100),
            call('cookies_total_size', 189),
        ], any_order=True)

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
            call('cookies.1.name', 'b_c'),
            call('cookies.1.size', 20),
            call('cookies.2.name', 'b_a'),
            call('cookies.2.size', 15),
            call('cookies.3.name', 'a'),
            call('cookies.3.size', 10),
            call('cookies.group.1.name', 'b'),
            call('cookies.group.1.size', 35),
            call('cookies.max.name', 'b_c'),
            call('cookies.max.size', 20),
            call('cookies.max.group.name', 'b'),
            call('cookies.max.group.size', 35),
            call('cookies_total_size', 45)
        ], any_order=True)

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring_no_cookies(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        mock_request = Mock()
        mock_request.COOKIES = {}

        middleware.process_request(mock_request)

        mock_set_custom_attribute.assert_has_calls([call('cookies_total_size', 0)], any_order=True)

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring_no_groups(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        mock_request = Mock()
        mock_request.COOKIES = {
            "a": "." * 10,
            "b": "." * 15,
        }

        middleware.process_request(mock_request)

        mock_set_custom_attribute.assert_has_calls([
            call('cookies.max.name', 'b'),
            call('cookies.max.size', 15),
            call('cookies.1.name', 'b'),
            call('cookies.1.size', 15),
            call('cookies.2.name', 'a'),
            call('cookies.2.size', 10),
            call('cookies_total_size', 25),
        ], any_order=True)


@ddt.ddt
class TestMonitor403Middleware(unittest.TestCase):
    """
    Tests for Monitor403Middleware
    """
    @ddt.data(True, False)
    def test_get_response(self, is_monitoring_enabled):
        response = HttpResponseForbidden()
        request = RequestFactory().get('/oauth2/exchange_access_token/google-oauth2/')

        middleware = Monitor403Middleware(lambda _: response)

        with patch('openedx.core.lib.request_utils.log') as mock_logger:
            with override_settings(ENABLE_403_MONITORING=is_monitoring_enabled):
                response = middleware(request)

        if is_monitoring_enabled:
            mock_logger.info.assert_called()
        else:
            mock_logger.info.assert_not_called()

    @ddt.data(True, False)
    def test_process_exception_requests_error(self, is_monitoring_enabled):
        request = RequestFactory().get('/oauth2/exchange_access_token/google-oauth2/')
        response = requests.models.Response()
        response.status_code = 403

        try:
            raise requests.exceptions.HTTPError('mock error message', response=response)
        except requests.exceptions.HTTPError as exception:
            with patch('openedx.core.lib.request_utils.log') as mock_logger:
                with override_settings(ENABLE_403_MONITORING=is_monitoring_enabled):
                    Monitor403Middleware('mock-response').process_exception(request, exception)

        if is_monitoring_enabled:
            mock_logger.info.assert_called()
        else:
            mock_logger.info.assert_not_called()

    @ddt.data(True, False)
    def test_process_exception_django_error(self, is_monitoring_enabled):
        request = RequestFactory().get('/oauth2/exchange_access_token/google-oauth2/')

        try:
            raise PermissionDenied()
        except PermissionDenied as exception:
            with patch('openedx.core.lib.request_utils.log') as mock_logger:
                with override_settings(ENABLE_403_MONITORING=is_monitoring_enabled):
                    Monitor403Middleware('mock-response').process_exception(request, exception)

        if is_monitoring_enabled:
            mock_logger.info.assert_called()
        else:
            mock_logger.info.assert_not_called()

    @ddt.data(True, False)
    def test_process_exception_drf_error(self, is_monitoring_enabled):
        request = RequestFactory().get('/oauth2/exchange_access_token/google-oauth2/')

        try:
            raise DRFPermissionDenied()
        except DRFPermissionDenied as exception:
            with patch('openedx.core.lib.request_utils.log') as mock_logger:
                with override_settings(ENABLE_403_MONITORING=is_monitoring_enabled):
                    Monitor403Middleware('mock-response').process_exception(request, exception)

        if is_monitoring_enabled:
            mock_logger.info.assert_called()
        else:
            mock_logger.info.assert_not_called()
