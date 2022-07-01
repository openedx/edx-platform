"""Tests for request_utils module."""

import unittest
from unittest.mock import Mock, call, patch

import ddt
import pytest
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edx_django_utils.cache import RequestCache

from openedx.core.lib.request_utils import (
    CookieMonitoringMiddleware,
    ExpectedErrorMiddleware,
    _get_expected_error_settings_dict,
    clear_cached_expected_error_settings,
    course_id_from_url,
    expected_error_exception_handler,
    get_request_or_stub,
    safe_get_host,
)


class RequestUtilTestCase(unittest.TestCase):
    """
    Tests for request_utils module.
    """
    def setUp(self):
        super().setUp()
        self.old_site_name = settings.SITE_NAME
        self.old_allowed_hosts = settings.ALLOWED_HOSTS

    def tearDown(self):
        super().tearDown()
        settings.SITE_NAME = self.old_site_name
        settings.ALLOWED_HOSTS = self.old_allowed_hosts

    def test_get_request_or_stub(self):
        """
        Outside the context of the request, we should still get a request
        that allows us to build an absolute URI.
        """
        stub = get_request_or_stub()
        expected_url = f"http://{settings.SITE_NAME}/foobar"
        assert stub.build_absolute_uri('foobar') == expected_url

    def test_safe_get_host(self):
        """ Tests that the safe_get_host function returns the desired host """
        settings.SITE_NAME = 'siteName.com'
        factory = RequestFactory()
        request = factory.request()
        request.META['HTTP_HOST'] = 'www.userProvidedHost.com'
        # If ALLOWED_HOSTS is not set properly, safe_get_host should return SITE_NAME
        settings.ALLOWED_HOSTS = None
        assert safe_get_host(request) == 'siteName.com'
        settings.ALLOWED_HOSTS = ["*"]
        assert safe_get_host(request) == 'siteName.com'
        settings.ALLOWED_HOSTS = ["foo.com", "*"]
        assert safe_get_host(request) == 'siteName.com'

        # If ALLOWED_HOSTS is set properly, and the host is valid, we just return the user-provided host
        settings.ALLOWED_HOSTS = [request.META['HTTP_HOST']]
        assert safe_get_host(request) == request.META['HTTP_HOST']

        # If ALLOWED_HOSTS is set properly but the host is invalid, we should get a SuspiciousOperation
        settings.ALLOWED_HOSTS = ["the_valid_website.com"]
        with pytest.raises(SuspiciousOperation):
            safe_get_host(request)

    def test_course_id_from_url(self):
        """ Test course_id_from_url(). """

        assert course_id_from_url('/login') is None
        assert course_id_from_url('/courses/edX/maths/') is None
        assert course_id_from_url('/api/courses/v1/blocks/edX/maths/2020') is None
        assert course_id_from_url('/api/courses/v1/blocks/course-v1:incidental+courseid+formatting') is None
        assert course_id_from_url('/api/courses/v41/notcourses/course-v1:incidental+courseid+formatting') is None

        course_id = course_id_from_url('/courses/course-v1:edX+maths+2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org="edX", course='maths', run='2020')

        course_id = course_id_from_url('/course/course-v1:edX+maths+2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org="edX", course='maths', run='2020')

        course_id = course_id_from_url('/courses/edX/maths/2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org='edX', course='maths', run='2020')

        course_id = course_id_from_url('/course/edX/maths/2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org="edX", course='maths', run='2020')

        course_id = course_id_from_url('/api/courses/v1/courses/course-v1:edX+maths+2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org='edX', course='maths', run='2020')

        course_id = course_id_from_url('/api/courses/v1/courses/edX/maths/2020')
        self.assertCourseIdFieldsMatch(course_id=course_id, org='edX', course='maths', run='2020')

    def assertCourseIdFieldsMatch(self, course_id, org, course, run):
        """ Asserts that the passed-in course id matches the specified fields"""
        assert course_id.org == org
        assert course_id.course == course
        assert course_id.run == run

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_basic_cookie_monitoring(self, mock_set_custom_attribute, mock_capture_cookie_sizes):
        mock_capture_cookie_sizes.is_enabled.return_value = False
        middleware = CookieMonitoringMiddleware()

        cookies_dict = {'a': 'b'}

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()

        middleware.process_request(mock_request)

        mock_set_custom_attribute.assert_called_once_with('cookies.header.size', 3)

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        cookies_dict = {
            "a": "." * 100,
            "_b": "." * 13,
            "_c_": "." * 13,
            "a.b": "." * 10,
            "a.c": "." * 10,
            "b.": "." * 13,
            "b_a": "." * 15,
            "b_c": "." * 15,
            "d": "." * 3,
        }

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()

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
            call('cookies.6.name', 'b.'),
            call('cookies.6.size', 13),
            call('cookies.7.name', 'a.b'),
            call('cookies.7.size', 10),
            call('cookies.8.name', 'a.c'),
            call('cookies.8.size', 10),
            call('cookies.group.1.name', 'b'),
            call('cookies.group.1.size', 43),
            call('cookies.group.2.name', 'a'),
            call('cookies.group.2.size', 20),
            call('cookies.max.name', 'a'),
            call('cookies.max.size', 100),
            call('cookies.max.group.name', 'a'),
            call('cookies.max.group.size', 100),
            call('cookies_total_size', 192),
            call('cookies_unaccounted_size', 3),
            call('cookies_total_num', 9),
            call('cookies.header.size', 238)
        ], any_order=True)

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring_max_group(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        cookies_dict = {
            "a": "." * 10,
            "b_a": "." * 15,
            "b_c": "." * 20,
        }

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()

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

        cookies_dict = {}

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()

        middleware.process_request(mock_request)

        mock_set_custom_attribute.assert_has_calls([
            call('cookies_total_size', 0),
            call('cookies.header.size', 0)
        ], any_order=True)

    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.set_custom_attribute")
    def test_cookie_monitoring_no_groups(self, mock_set_custom_attribute, mock_capture_cookie_sizes):

        mock_capture_cookie_sizes.is_enabled.return_value = True
        middleware = CookieMonitoringMiddleware()

        cookies_dict = {
            "a": "." * 10,
            "b": "." * 15,
        }

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()

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

    @override_settings(COOKIE_SIZE_LOGGING_THRESHOLD=1)
    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.encrypt_for_log")
    def test_log_encrypted_cookies_no_key(self, mock_encrypt, mock_capture_cookie_sizes):
        middleware = CookieMonitoringMiddleware()

        cookies_dict = {
            "a": "." * 10,
            "b": "." * 15,
        }

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()

        middleware.process_request(mock_request)
        mock_encrypt.assert_not_called()

    @override_settings(COOKIE_SIZE_LOGGING_THRESHOLD=1)
    @override_settings(COOKIE_HEADER_DEBUG_PUBLIC_KEY="fake-key")
    @patch("openedx.core.lib.request_utils.CAPTURE_COOKIE_SIZES")
    @patch("openedx.core.lib.request_utils.encrypt_for_log")
    def test_log_encrypted_cookies(self, mock_encrypt, mock_capture_cookie_sizes):

        middleware = CookieMonitoringMiddleware()

        cookies_dict = {
            "a": "." * 10,
            "b": "." * 15,
        }

        factory = RequestFactory()
        for name, value in cookies_dict.items():
            factory.cookies[name] = value

        mock_request = factory.request()
        cookie_header = str(mock_request.META.get('HTTP_COOKIE', ''))

        middleware.process_request(mock_request)
        mock_encrypt.assert_has_calls([
            call(cookie_header, "fake-key")
        ])


class TestGetExpectedErrorSettingsDict(unittest.TestCase):
    """
    Tests for processing issues in _get_expected_error_settings_dict()

    Note: Although this is a private method, we have broken out the testing of
      special cases so they don't have to be tested with the middleware and drf
      custom error handler.
    """
    def setUp(self):
        super().setUp()
        clear_cached_expected_error_settings()

    def test_get_with_no_setting(self):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        assert expected_error_settings_dict == {}

    @override_settings(EXPECTED_ERRORS=[])
    def test_get_with_empty_list_setting(self):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        assert expected_error_settings_dict == {}

    @patch('openedx.core.lib.request_utils.log')
    @override_settings(EXPECTED_ERRORS=[{}])
    def test_get_with_missing_module_and_class(self, mock_logger):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        mock_logger.error.assert_called_once_with(
            "Skipping EXPECTED_ERRORS[%d] setting. 'MODULE_AND_CLASS' set to [%s] and should be module.Class, like "
            "'rest_framework.exceptions.PermissionDenied'.",
            0,
            None,
        )
        assert expected_error_settings_dict == {}

    @patch('openedx.core.lib.request_utils.log')
    @override_settings(EXPECTED_ERRORS=[
        {
            'MODULE_AND_CLASS': 'colon.separator.warning:Class',
            'REASON_EXPECTED': 'Because',
        }
    ])
    def test_get_with_colon_in_class_and_module(self, mock_logger):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        mock_logger.warning.assert_called_once_with(
            "Replacing ':' with '.' in EXPECTED_ERRORS[%d]['MODULE_AND_CLASS'], which was set to %s. Note that "
            "monitoring and logging will not include the ':'.",
            0,
            'colon.separator.warning:Class',
        )
        assert 'colon.separator.warning.Class' in expected_error_settings_dict

    @patch('openedx.core.lib.request_utils.log')
    @override_settings(EXPECTED_ERRORS=[
        {
            'MODULE_AND_CLASS': 'valid.module.DuplicateClass',
            'REASON_EXPECTED': 'Because'
        },
        {
            'MODULE_AND_CLASS': 'valid.module.DuplicateClass',
            'REASON_EXPECTED': 'Because overridden'
        },
    ])
    def test_get_with_duplicate_class_and_module(self, mock_logger):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        mock_logger.warning.assert_called_once_with(
            "EXPECTED_ERRORS[%d] setting is overriding an earlier setting. 'MODULE_AND_CLASS' [%s] is defined "
            "multiple times.",
            1,
            'valid.module.DuplicateClass',
        )
        assert 'valid.module.DuplicateClass' in expected_error_settings_dict
        assert expected_error_settings_dict['valid.module.DuplicateClass']['reason_expected'] == 'Because overridden'

    @patch('openedx.core.lib.request_utils.log')
    @override_settings(EXPECTED_ERRORS=[{'MODULE_AND_CLASS': 'valid.module.and.class.ButMissingReason'}])
    def test_get_with_missing_reason(self, mock_logger):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        mock_logger.error.assert_called_once_with(
            "Skipping EXPECTED_ERRORS[%d] setting. 'REASON_EXPECTED' is required to document why %s is an expected "
            "error.",
            0, 'valid.module.and.class.ButMissingReason'
        )
        assert expected_error_settings_dict == {}

    @patch('openedx.core.lib.request_utils.log')
    @override_settings(EXPECTED_ERRORS=['not-a-dict'])
    def test_get_with_invalid_dict(self, mock_logger):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        mock_logger.exception.assert_called_once_with(
            'Error processing setting EXPECTED_ERRORS. AttributeError("\'str\' object has no attribute \'get\'")'
        )
        assert expected_error_settings_dict == {}

    @override_settings(EXPECTED_ERRORS=[{
        'MODULE_AND_CLASS': 'test.module.TestClass',
        'REASON_EXPECTED': 'Because'
    }])
    def test_get_with_defaults(self):
        expected_error_settings_dict = _get_expected_error_settings_dict()
        assert expected_error_settings_dict == {
            'test.module.TestClass': {
                'is_ignored': True,
                'log_error': False,
                'log_stack_trace': False,
                'reason_expected': 'Because'
            }
        }


class CustomError1(Exception):
    pass


class CustomError2(Exception):
    pass


@ddt.ddt
class TestExpectedErrorMiddleware(unittest.TestCase):
    """
    Tests for ExpectedErrorMiddleware
    """
    def setUp(self):
        super().setUp()
        RequestCache.clear_all_namespaces()
        clear_cached_expected_error_settings()
        self.mock_request = RequestFactory().get('/test')
        self.mock_exception = CustomError1('Test failure')

    def test_get_response(self):
        expected_response = Mock()

        middleware = ExpectedErrorMiddleware(lambda _: expected_response)
        response = middleware(self.mock_request)

        assert response == expected_response

    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @patch('openedx.core.lib.request_utils.log')
    def test_process_exception_no_expected_errors(self, mock_logger, mock_set_custom_attribute):
        ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, self.mock_exception)

        mock_logger.info.assert_not_called()
        mock_set_custom_attribute.assert_not_called()

    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @patch('openedx.core.lib.request_utils.log')
    @ddt.data(None, [])
    def test_process_exception_with_empty_expected_errors(
        self, expected_errors_setting, mock_logger, mock_set_custom_attribute,
    ):
        with override_settings(EXPECTED_ERRORS=expected_errors_setting):
            ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, self.mock_exception)

        mock_logger.info.assert_not_called()
        mock_set_custom_attribute.assert_not_called()

    @override_settings(EXPECTED_ERRORS=[{
        'MODULE_AND_CLASS': 'test.module.TestException',
        'REASON_EXPECTED': 'Because',
    }])
    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @patch('openedx.core.lib.request_utils.log')
    def test_process_exception_not_matching_expected_errors(self, mock_logger, mock_set_custom_attribute):
        ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, self.mock_exception)

        mock_logger.info.assert_not_called()
        mock_set_custom_attribute.assert_called_once_with('checked_error_expected_from', 'middleware')

    @override_settings(EXPECTED_ERRORS=[
        {
            'MODULE_AND_CLASS': 'test.module.TestException',
            'REASON_EXPECTED': 'Because',
        },
        {
            'MODULE_AND_CLASS': 'openedx.core.lib.tests.test_request_utils.CustomError1',
            'REASON_EXPECTED': 'Because',
        }
    ])
    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @patch('openedx.core.lib.request_utils.log')
    def test_process_exception_expected_error_with_defaults(self, mock_logger, mock_set_custom_attribute):
        ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, self.mock_exception)

        mock_logger.info.assert_not_called()
        mock_set_custom_attribute.assert_has_calls(
            [
                call('checked_error_expected_from', 'middleware'),
                call('error_expected', True),
                call('error_ignored_class', 'openedx.core.lib.tests.test_request_utils.CustomError1'),
                call('error_ignored_message', 'Test failure'),
            ],
            any_order=True
        )

    @override_settings(EXPECTED_ERRORS=[
        {
            'MODULE_AND_CLASS': 'openedx.core.lib.tests.test_request_utils.CustomError1',
            'REASON_EXPECTED': 'Because',
        },
        {
            'MODULE_AND_CLASS': 'openedx.core.lib.tests.test_request_utils.CustomError2',
            'REASON_EXPECTED': 'Because',
        }
    ])
    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @ddt.data(True, False)
    def test_process_exception_called_multiple_times(self, use_same_exception, mock_set_custom_attribute):
        mock_first_exception = self.mock_exception
        mock_second_exception = mock_first_exception if use_same_exception else CustomError2("Oops")

        ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, mock_first_exception)
        ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, mock_second_exception)

        expected_calls = [
            call('checked_error_expected_from', 'middleware'),
            call('error_expected', True),
            call('error_ignored_class', 'openedx.core.lib.tests.test_request_utils.CustomError1'),
            call('error_ignored_message', 'Test failure'),
            call('checked_error_expected_from', 'middleware'),
        ]
        if use_same_exception:
            expected_calls += [call('checked_error_expected_from', 'multiple')]
        else:
            expected_calls += [
                call('unexpected_multiple_exceptions', 'openedx.core.lib.tests.test_request_utils.CustomError1'),
            ]
        mock_set_custom_attribute.assert_has_calls(expected_calls)
        assert mock_set_custom_attribute.call_count == len(expected_calls)

    @override_settings(EXPECTED_ERRORS=[{
        'MODULE_AND_CLASS': 'Exception',
        'REASON_EXPECTED': 'Because',
    }])
    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    def test_process_exception_with_plain_exception(self, mock_set_custom_attribute):
        mock_exception = Exception("Oops")
        ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, mock_exception)

        mock_set_custom_attribute.assert_has_calls([
            call('error_expected', True),
            call('error_ignored_class', 'Exception'),
            call('error_ignored_message', 'Oops'),
        ])

    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @patch('openedx.core.lib.request_utils.log')
    @ddt.data(
        (False, True),  # skip logging
        (True, False),  # log without stacktrace
        (True, True),   # log with stacktrace
    )
    @ddt.unpack
    def test_process_exception_expected_error_with_overrides(
        self, log_error, log_stack_trace, mock_logger, mock_set_custom_attribute,
    ):
        expected_class = 'openedx.core.lib.tests.test_request_utils.CustomError1'
        expected_message = 'Test failure'

        with override_settings(EXPECTED_ERRORS=[{
            'MODULE_AND_CLASS': expected_class,
            'IS_IGNORED': False,
            'LOG_ERROR': log_error,
            'LOG_STACK_TRACE': log_stack_trace,
            'REASON_EXPECTED': 'Because',
        }]):
            ExpectedErrorMiddleware('mock-response').process_exception(self.mock_request, self.mock_exception)

        if log_error:
            exc_info = self.mock_exception if log_stack_trace else None
            mock_logger.info.assert_called_once_with(
                'Expected error %s: %s: seen for path %s', expected_class, expected_message, '/test', exc_info=exc_info
            )
        else:
            mock_logger.info.assert_not_called()
        mock_set_custom_attribute.assert_has_calls(
            [
                call('checked_error_expected_from', 'middleware'),
                call('error_expected', True),
            ],
            any_order=True
        )


@ddt.ddt
class TestExpectedErrorExceptionHandler(unittest.TestCase):
    """
    Tests for expected_error_exception_handler.

    Note: Only smoke tests the handler to not duplicate all testing in TestExpectedErrorMiddleware.
    """
    def setUp(self):
        super().setUp()
        RequestCache.clear_all_namespaces()
        clear_cached_expected_error_settings()
        self.mock_request = RequestFactory().get('/test')
        self.mock_exception = CustomError1('Test failure')

    @override_settings(EXPECTED_ERRORS=[{
        'MODULE_AND_CLASS': 'openedx.core.lib.tests.test_request_utils.CustomError1',
        'LOG_ERROR': True,
        'REASON_EXPECTED': 'Because',
    }])
    @patch('openedx.core.lib.request_utils.set_custom_attribute')
    @patch('openedx.core.lib.request_utils.log')
    @ddt.data(True, False)
    def test_handler_with_expected_error(
        self, use_valid_context, mock_logger, mock_set_custom_attribute
    ):
        if use_valid_context:
            mock_context = {'request': self.mock_request}
            expected_request_path = '/test'
        else:
            mock_context = None
            expected_request_path = 'request-path-unknown'
        expected_error_exception_handler(self.mock_exception, mock_context)

        expected_class = 'openedx.core.lib.tests.test_request_utils.CustomError1'
        expected_message = 'Test failure'
        mock_logger.info.assert_called_once_with(
            'Expected error %s: %s: seen for path %s',
            expected_class,
            expected_message,
            expected_request_path,
            exc_info=None,
        )
        mock_set_custom_attribute.assert_has_calls(
            [
                call('checked_error_expected_from', 'drf'),
                call('error_expected', True),
                call('error_ignored_class', expected_class),
                call('error_ignored_message', expected_message),
            ],
            any_order=True
        )
