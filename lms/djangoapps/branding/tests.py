"""
Tests for branding page
"""
import datetime
from django.http import HttpResponseRedirect
from pytz import UTC
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings
from django.test.client import RequestFactory

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
import student.views
from branding.views import index
from edxmako.tests import mako_middleware_process_request
from mock import patch
from student.tests.factories import UserFactory
from student.models import CourseEnrollment

FEATURES_WITH_STARTDATE = settings.FEATURES.copy()
FEATURES_WITH_STARTDATE['DISABLE_START_DATES'] = False
FEATURES_WO_STARTDATE = settings.FEATURES.copy()
FEATURES_WO_STARTDATE['DISABLE_START_DATES'] = True


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class AnonymousIndexPageTest(ModuleStoreTestCase):
    """
    Tests that anonymous users can access the '/' page,  Need courses with start date
    """
    def setUp(self):
        super(AnonymousIndexPageTest, self).setUp()
        self.factory = RequestFactory()
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.course = CourseFactory.create(
            days_early_for_beta=5,
            enrollment_start=datetime.datetime.now(UTC) + datetime.timedelta(days=3),
            user_id=self.user.id,
        )

    @override_settings(FEATURES=FEATURES_WITH_STARTDATE)
    def test_none_user_index_access_with_startdate_fails(self):
        """
        This is a regression test for a bug where the incoming user is
        anonymous and start dates are being checked.  It replaces a previous
        test as it solves the issue in a different way
        """
        request = self.factory.get('/')
        request.user = AnonymousUser()

        mako_middleware_process_request(request)
        student.views.index(request)

    @override_settings(FEATURES=FEATURES_WITH_STARTDATE)
    def test_anon_user_with_startdate_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @override_settings(FEATURES=FEATURES_WO_STARTDATE)
    def test_anon_user_no_startdate_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @patch.dict('django.conf.settings.FEATURES', {'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER': True})
    @patch.dict('django.conf.settings.FEATURES', {'REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES': False})
    def test_redirects_homepage_to_dashboard_if_always_redirect_flag_is_set_to_true(self):
        """
        Check when user clicks on homepage then he will be redirected to dashboard if only the flag
        ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER set to True.
        """
        self.client.login(username=self.user.username, password="password")
        response = self.client.get('/')
        self.assertRedirects(response, '/dashboard')

    @patch.dict('django.conf.settings.FEATURES', {'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER': False})
    @patch.dict('django.conf.settings.FEATURES', {'REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES': True})
    def test_redirects_homepage_to_dashboard_if_enrolled_in_courses(self):
        """
        Check when user clicks on homepage then he will be redirected to dashboard if the flag
        REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES is set to True and User is also enrolled in any course.
        """
        CourseEnrollment.enroll(self.user, self.course.id)
        self.client.login(username=self.user.username, password="password")
        response = self.client.get('/')
        self.assertRedirects(response, '/dashboard')

    @patch.dict('django.conf.settings.FEATURES', {'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER': False})
    @patch.dict('django.conf.settings.FEATURES', {'REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES': True})
    def test_does_not_redirect_homepage_to_dashboard_if_user_not_enrolled_in_courses(self):
        """
        Check when user clicks on homepage then he will not be redirected to dashboard even if the flag
        REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES is set to True but the user is not enrolled in any course.
        """
        self.client.login(username=self.user.username, password="password")
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)

    @patch.dict('django.conf.settings.FEATURES', {'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER': False})
    @patch.dict('django.conf.settings.FEATURES', {'REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES': False})
    def test_does_not_redirect_homepage_to_dashboard_if_user_enrolled_in_courses(self):
        """
        Check when user clicks on homepage then he will not be redirected to dashboard even if user enrolled in courses
        but the flag REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES is not set to True.
        """
        CourseEnrollment.enroll(self.user, self.course.id)
        self.client.login(username=self.user.username, password="password")
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)

    @patch.dict('django.conf.settings.FEATURES', {'ALWAYS_REDIRECT_HOMEPAGE_TO_DASHBOARD_FOR_AUTHENTICATED_USER': False})
    @patch.dict('django.conf.settings.FEATURES', {'REDIRECT_HOMEPAGE_TO_DASHBOARD_IF_ENROLLED_IN_COURSES': False})
    def test_does_not_redirect_homepage_to_dashboard(self):
        """
        Check when user clicks on homepage then he will not be redirected to dashboard if none of the flag is set and
        also user is not enrolled in any courses.
        """
        self.client.login(username=self.user.username, password="password")
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)


    def test_allow_x_frame_options(self):
        """
        Check the x-frame-option response header
        """

        # check to see that the default setting is to ALLOW iframing
        resp = self.client.get('/')
        self.assertEquals(resp['X-Frame-Options'], 'ALLOW')

    @override_settings(X_FRAME_OPTIONS='DENY')
    def test_deny_x_frame_options(self):
        """
        Check the x-frame-option response header
        """

        # check to see that the override value is honored
        resp = self.client.get('/')
        self.assertEquals(resp['X-Frame-Options'], 'DENY')

    def test_edge_redirect_to_login(self):
        """
        Test edge homepage redirect to lms login.
        """

        request = self.factory.get('/')
        request.user = AnonymousUser()

        # HTTP Host changed to edge.
        request.META["HTTP_HOST"] = "edge.edx.org"
        response = index(request)

        # Response should be instance of HttpResponseRedirect.
        self.assertIsInstance(response, HttpResponseRedirect)
        # Location should be "/login".
        self.assertEqual(response._headers.get("location")[1], "/login")
