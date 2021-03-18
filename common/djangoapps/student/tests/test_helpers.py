""" Test Student helpers """


import logging
import unittest
from collections import OrderedDict
from unittest.mock import patch

import ddt
from completion.test_utils import CompletionWaffleTestMixin, submit_completions_for_testing
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from opaque_keys.edx.locator import BlockUsageLocator
from testfixtures import LogCapture

from common.djangoapps.student.helpers import get_next_url_for_login_page, get_resume_urls_for_enrollments
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

LOGGER_NAME = "common.djangoapps.student.helpers"


@ddt.ddt
class TestLoginHelper(TestCase):
    """Test login helper methods."""
    static_url = settings.STATIC_URL

    def setUp(self):
        super().setUp()
        self.request = RequestFactory()

    @staticmethod
    def _add_session(request):
        """Annotate the request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

    @ddt.data(
        (logging.WARNING, "WARNING", "https://www.amazon.com", "text/html", None,
         "Unsafe redirect parameter detected after login page: 'https://www.amazon.com'"),
        (logging.WARNING, "WARNING", "testserver/edx.org/images/logo", "text/html", None,
         "Redirect to theme content detected after login page: 'testserver/edx.org/images/logo'"),
        (logging.INFO, "INFO", "favicon.ico", "image/*", "test/agent",
         "Redirect to non html content 'image/*' detected from 'test/agent' after login page: 'favicon.ico'"),
        (logging.WARNING, "WARNING", "https://www.test.com/test.jpg", "image/*", None,
         "Unsafe redirect parameter detected after login page: 'https://www.test.com/test.jpg'"),
        (logging.INFO, "INFO", static_url + "dummy.png", "image/*", "test/agent",
         "Redirect to non html content 'image/*' detected from 'test/agent' after login page: '" + static_url +
         "dummy.png" + "'"),
        (logging.WARNING, "WARNING", "test.png", "text/html", None,
         "Redirect to url path with specified file type 'image/png' not allowed: 'test.png'"),
        (logging.WARNING, "WARNING", static_url + "dummy.png", "text/html", None,
         "Redirect to url path with specified file type 'image/png' not allowed: '" + static_url + "dummy.png" + "'"),
    )
    @ddt.unpack
    def test_next_failures(self, log_level, log_name, unsafe_url, http_accept, user_agent, expected_log):
        """ Test unsafe next parameter """
        with LogCapture(LOGGER_NAME, level=log_level) as logger:
            req = self.request.get(settings.LOGIN_URL + f"?next={unsafe_url}")
            req.META["HTTP_ACCEPT"] = http_accept
            req.META["HTTP_USER_AGENT"] = user_agent
            get_next_url_for_login_page(req)
            logger.check(
                (LOGGER_NAME, log_name, expected_log)
            )

    @ddt.data(
        ('/dashboard', 'text/html', 'testserver'),
        ('https://edx.org/courses', 'text/*', 'edx.org'),
        ('https://test.edx.org/courses', '*/*', 'edx.org'),
        ('https://test2.edx.org/courses', 'image/webp, */*;q=0.8', 'edx.org'),
    )
    @ddt.unpack
    @override_settings(LOGIN_REDIRECT_WHITELIST=['test.edx.org', 'test2.edx.org'])
    def test_safe_next(self, next_url, http_accept, host):
        """ Test safe next parameter """
        req = self.request.get(settings.LOGIN_URL + f"?next={next_url}", HTTP_HOST=host)
        req.META["HTTP_ACCEPT"] = http_accept
        next_page = get_next_url_for_login_page(req)
        assert next_page == next_url

    tpa_hint_test_cases = [
        # Test requests outside the TPA pipeline - tpa_hint should be added.
        (None, '/dashboard', '/dashboard', False),
        ('', '/dashboard', '/dashboard', False),
        ('', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', False),
        ('saml-idp', '/dashboard', '/dashboard?tpa_hint=saml-idp', False),
        # THIRD_PARTY_AUTH_HINT can be overridden via the query string
        ('saml-idp', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', False),

        # Test requests inside the TPA pipeline - tpa_hint should not be added, preventing infinite loop.
        (None, '/dashboard', '/dashboard', True),
        ('', '/dashboard', '/dashboard', True),
        ('', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', True),
        ('saml-idp', '/dashboard', '/dashboard', True),
        # OK to leave tpa_hint overrides in place.
        ('saml-idp', '/dashboard?tpa_hint=oa2-google-oauth2', '/dashboard?tpa_hint=oa2-google-oauth2', True),
    ]
    tpa_hint_test_cases_with_method = [
        (method, *test_case)
        for test_case in tpa_hint_test_cases
        for method in ['GET', 'POST']
    ]

    @patch('common.djangoapps.student.helpers.third_party_auth.pipeline.get')
    @ddt.data(*tpa_hint_test_cases_with_method)
    @ddt.unpack
    def test_third_party_auth_hint(
        self,
        method,
        tpa_hint,
        next_url,
        expected_url,
        running_pipeline,
        mock_running_pipeline,
    ):
        mock_running_pipeline.return_value = running_pipeline

        def validate_login():
            """
            Assert that get_next_url_for_login_page returns as expected.
            """
            if method == 'GET':
                req = self.request.get(settings.LOGIN_URL + f"?next={next_url}")
            elif method == 'POST':
                req = self.request.post(settings.LOGIN_URL, {'next': next_url})
            req.META["HTTP_ACCEPT"] = "text/html"
            self._add_session(req)
            next_page = get_next_url_for_login_page(req)
            assert next_page == expected_url

        with override_settings(FEATURES=dict(settings.FEATURES, THIRD_PARTY_AUTH_HINT=tpa_hint)):
            validate_login()

        with with_site_configuration_context(configuration=dict(THIRD_PARTY_AUTH_HINT=tpa_hint)):
            validate_login()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    @ddt.data(
        (None, '/dashboard'),
        ('invalid-url', '/dashboard'),
        ('courses', '/courses'),
    )
    @ddt.unpack
    def test_custom_redirect_url(self, redirect, expected_url):
        """
        Test custom redirect after login
        """
        configuration_values = {"DEFAULT_REDIRECT_AFTER_LOGIN": redirect}
        req = self.request.get(settings.LOGIN_URL)
        req.META["HTTP_ACCEPT"] = "text/html"

        with with_site_configuration_context(configuration=configuration_values):
            next_page = get_next_url_for_login_page(req)

        assert next_page == expected_url


class TestResumeURLs(SharedModuleStoreTestCase, CompletionWaffleTestMixin):
    """Test enrollment resume URL generation"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_1 = CourseFactory.create(course='resume_course_1')
        cls.course_2 = CourseFactory.create(course='resume_course_2')

    def setUp(self):
        super().setUp()
        self.override_waffle_switch(True)
        self.user = UserFactory()
        self.enrollments = [
            CourseEnrollmentFactory.create(user=self.user, course_id=self.course_1.id),
            CourseEnrollmentFactory.create(user=self.user, course_id=self.course_2.id),
        ]

    def _course_problems(self, course):
        return [
            ItemFactory.create(
                category='problem',
                parent_location=course.location,
                display_name='problem_1'
            ).location,
            ItemFactory.create(
                category='problem',
                parent_location=course.location,
                display_name='problem_2'
            ).location,
        ]

    def test_enrollments_no_completion(self):
        """ Enrollments with no completion return empty string """
        resume_urls = get_resume_urls_for_enrollments(self.user, self.enrollments)
        expected = OrderedDict([
            (self.course_1.id, ''),
            (self.course_2.id, ''),
        ])
        self.assertEqual(resume_urls, expected)

    def test_enrollments_with_completion(self):
        """ Enrollment with completion data should return block URL """
        course_1_problem_blocks = self._course_problems(self.course_1)
        course_2_problem_blocks = self._course_problems(self.course_2)
        submit_completions_for_testing(self.user, course_1_problem_blocks + course_2_problem_blocks)
        resume_urls = get_resume_urls_for_enrollments(self.user, self.enrollments)
        self.assertIn('resume_course_1/problem/problem_2', resume_urls[self.course_1.id])
        self.assertIn('resume_course_2/problem/problem_2', resume_urls[self.course_2.id])

    def test_enrollment_with_completion_does_not_exist(self):
        """
        Enrollment with completion block that no longer exists
        should return empty string
        """
        problem_locator = BlockUsageLocator(self.course_1.id, block_type='problem', block_id='problem_dne')
        course_2_problem_blocks = self._course_problems(self.course_2)
        submit_completions_for_testing(self.user, [problem_locator] + course_2_problem_blocks)
        resume_urls = get_resume_urls_for_enrollments(self.user, self.enrollments)
        self.assertIn('', resume_urls[self.course_1.id])
        self.assertIn('resume_course_2/problem/problem_2', resume_urls[self.course_2.id])

    def test_enrollment_with_completion_inaccessible(self):
        """
        Enrollment with completion block that is not accessible
        should return empty string
        """
        course_1_problem_blocks = self._course_problems(self.course_1)
        course_2_problem_blocks = self._course_problems(self.course_2)
        submit_completions_for_testing(self.user, course_1_problem_blocks + course_2_problem_blocks)
        staff_problem = self.store.get_item(course_1_problem_blocks[-1])
        staff_problem.visible_to_staff_only = True
        self.store.update_item(staff_problem, self.user.id)
        resume_urls = get_resume_urls_for_enrollments(self.user, self.enrollments)
        self.assertIn('', resume_urls[self.course_1.id])
        self.assertIn('resume_course_2/problem/problem_2', resume_urls[self.course_2.id])
