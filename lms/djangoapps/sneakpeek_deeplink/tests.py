"""
Tests for deeplink middleware for sneakpeek
"""
import mock
import pygeoip
import unittest
from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase, Client
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser
from django.utils.importlib import import_module
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.models import CourseEnrollment, UserProfile
from courseware.models import CoursePreference
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory

from sneakpeek_deeplink.middleware import SneakPeekDeepLinkMiddleware

NO_SNEAKPEEK_PATHS = [
    '/courses/open/course/run/lti_rest_endpoints/',  # lti_rest_endpoint
    '/courses/open/course/run/xblock/usage_id/handler_noauth/handler',  # xblock_handler_noauth
    '/courses/open/course/run/xqueue/user_id/mod_id/dispatch',
]

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class SneakPeekDeeplinkMiddlewareTests(TestCase):
    """
    Tests of Sneakpek deeplink middleware
    """
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.middleware = SneakPeekDeepLinkMiddleware()
        month = timedelta(days=30)
        month2 = timedelta(days=60)
        now = datetime.now()
        self.nonsneakpeek_course = CourseFactory.create(
            org='nonsneakpeek',
            number='course',
            run='run',
            enrollment_start=now - month,
            enrollment_end=now + month)
        self.nonsneakpeek_course.save()
        self.open_course = CourseFactory.create(
            org='open',
            number='course',
            run='run',
            enrollment_start=now - month,
            enrollment_end=now + month)
        self.open_course.save()
        self.closed_course = CourseFactory.create(
            org='closed',
            number='course',
            run='run',
            enrollment_start=now - month2,
            enrollment_end=now - month)
        self.closed_course.save()
        CoursePreference(
            course_id=self.open_course.id,
            pref_key="allow_nonregistered_access",
            pref_value="true",
        ).save()
        CoursePreference(
            course_id=self.closed_course.id,
            pref_key="allow_nonregistered_access",
            pref_value="true",
        ).save()

    def make_successful_sneakpeek_login_request(self):
        """
        This returns a request which will cause a sneakpeek to happen
        """
        sneakpeek_path = '/courses/open/course/run/info'
        req = self.factory.get(sneakpeek_path)
        req.session = import_module(settings.SESSION_ENGINE).SessionStore()  # empty session
        req.user = AnonymousUser()
        return req

    def assertSuccessfulSneakPeek(self, request, course):
        self.assertTrue(request.user.is_authenticated())
        self.assertFalse(UserProfile.has_registered(request.user))
        self.assertTrue(CourseEnrollment.is_enrolled(request.user, course.id))

    def assertNoSneakPeek(self, request, course, check_auth=True):
        if check_auth:
            self.assertFalse(request.user.is_authenticated())
        self.assertEquals(0, CourseEnrollment.objects.filter(course_id=course.id).count())

    def test_sneakpeek_success(self):
        req = self.make_successful_sneakpeek_login_request()
        self.assertIsNone(self.middleware.process_request(req))
        self.assertSuccessfulSneakPeek(req, self.open_course)

    def test_non_get(self):
        req = self.make_successful_sneakpeek_login_request()
        req.method = "POST"
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    def test_get_404(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = '/foobarmew'
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    def test_url_blacklists(self):
        for path in NO_SNEAKPEEK_PATHS:
            req = self.make_successful_sneakpeek_login_request()
            req.path = path
            self.assertIsNone(self.middleware.process_request(req))
            self.assertNoSneakPeek(req, self.open_course)

    def test_authenticated_user(self):
        req = self.make_successful_sneakpeek_login_request()
        user = UserFactory()
        user.save()
        req.user = user
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course, check_auth=False)

    def test_noncourse_path(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = "/dashboard"
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    def test_nonsneakpeek_course(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = '/courses/nonsneakpeek/course/run/info'
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.nonsneakpeek_course)

    def test_sneakpeek_course_enrollment_closed(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = '/courses/closed/course/run/info'
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.closed_course)
