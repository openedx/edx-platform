"""Tests for the login and registration form rendering. """
import urllib
import unittest

import ddt
from mock import patch
from django.conf import settings
from django.core.urlresolvers import reverse

from util.testing import UrlResetMixin
from xmodule.modulestore.tests.factories import CourseFactory
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

# This relies on third party auth being enabled in the test
# settings with the feature flag `ENABLE_THIRD_PARTY_AUTH`
THIRD_PARTY_AUTH_BACKENDS = ["google-oauth2", "facebook"]
THIRD_PARTY_AUTH_PROVIDERS = ["Google", "Facebook"]


def _third_party_login_url(backend_name, auth_entry, redirect_url=None):
    """Construct the login URL to start third party authentication. """
    params = [("auth_entry", auth_entry)]
    if redirect_url:
        params.append(("next", redirect_url))

    return u"{url}?{params}".format(
        url=reverse("social:begin", kwargs={"backend": backend_name}),
        params=urllib.urlencode(params)
    )


def _finish_auth_url(params):
    """ Construct the URL that follows login/registration if we are doing auto-enrollment """
    return u"{}?{}".format(reverse('finish_auth'), urllib.urlencode(params))


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class LoginFormTest(ThirdPartyAuthTestMixin, UrlResetMixin, SharedModuleStoreTestCase):
    """Test rendering of the login form. """

    URLCONF_MODULES = ['lms.urls']

    @classmethod
    def setUpClass(cls):
        super(LoginFormTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @patch.dict(settings.FEATURES, {"ENABLE_COMBINED_LOGIN_REGISTRATION": False})
    def setUp(self):
        super(LoginFormTest, self).setUp()

        self.url = reverse("signin_user")
        self.course_id = unicode(self.course.id)
        self.courseware_url = reverse("courseware", args=[self.course_id])
        self.configure_google_provider(enabled=True, visible=True)
        self.configure_facebook_provider(enabled=True, visible=True)

    @patch.dict(settings.FEATURES, {"ENABLE_THIRD_PARTY_AUTH": False})
    @ddt.data(THIRD_PARTY_AUTH_PROVIDERS)
    def test_third_party_auth_disabled(self, provider_name):
        response = self.client.get(self.url)
        self.assertNotContains(response, provider_name)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_third_party_auth_no_course_id(self, backend_name):
        response = self.client.get(self.url)
        expected_url = _third_party_login_url(backend_name, "login")
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_third_party_auth_with_course_id(self, backend_name):
        # Provide a course ID to the login page, simulating what happens
        # when a user tries to enroll in a course without being logged in
        params = [('course_id', self.course_id)]
        response = self.client.get(self.url, params)

        # Expect that the course ID is added to the third party auth entry
        # point, so that the pipeline will enroll the student and
        # redirect the student to the track selection page.
        expected_url = _third_party_login_url(
            backend_name,
            "login",
            redirect_url=_finish_auth_url(params),
        )
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_courseware_redirect(self, backend_name):
        # Try to access courseware while logged out, expecting to be
        # redirected to the login page.
        response = self.client.get(self.courseware_url, follow=True)
        self.assertRedirects(
            response,
            u"{url}?next={redirect_url}".format(
                url=reverse("signin_user"),
                redirect_url=self.courseware_url
            )
        )

        # Verify that the third party auth URLs include the redirect URL
        # The third party auth pipeline will redirect to this page
        # once the user successfully authenticates.
        expected_url = _third_party_login_url(
            backend_name,
            "login",
            redirect_url=self.courseware_url
        )
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_third_party_auth_with_params(self, backend_name):
        params = [
            ('course_id', self.course_id),
            ('enrollment_action', 'enroll'),
            ('course_mode', 'honor'),
            ('email_opt_in', 'true'),
            ('next', '/custom/final/destination'),
        ]
        response = self.client.get(self.url, params)
        expected_url = _third_party_login_url(
            backend_name,
            "login",
            redirect_url=_finish_auth_url(params),
        )
        self.assertContains(response, expected_url)

    @ddt.data(None, "true", "false")
    def test_params(self, opt_in_value):
        params = [
            ('course_id', self.course_id),
            ('enrollment_action', 'enroll'),
            ('course_mode', 'honor'),
            ('email_opt_in', opt_in_value),
            ('next', '/custom/final/destination'),
        ]

        # Get the login page
        response = self.client.get(self.url, params)

        # Verify that the parameters are sent on to the next page correctly
        post_login_handler = _finish_auth_url(params)
        js_success_var = 'var nextUrl = "{}";'.format(post_login_handler)
        self.assertContains(response, js_success_var)

        # Verify that the login link preserves the querystring params
        login_link = u"{url}?{params}".format(
            url=reverse('signin_user'),
            params=urllib.urlencode([('next', post_login_handler)])
        )
        self.assertContains(response, login_link)


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class RegisterFormTest(ThirdPartyAuthTestMixin, UrlResetMixin, SharedModuleStoreTestCase):
    """Test rendering of the registration form. """

    URLCONF_MODULES = ['lms.urls']

    @classmethod
    def setUpClass(cls):
        super(RegisterFormTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    @patch.dict(settings.FEATURES, {"ENABLE_COMBINED_LOGIN_REGISTRATION": False})
    def setUp(self):
        super(RegisterFormTest, self).setUp()

        self.url = reverse("register_user")
        self.course_id = unicode(self.course.id)
        self.configure_google_provider(enabled=True, visible=True)
        self.configure_facebook_provider(enabled=True, visible=True)

    @patch.dict(settings.FEATURES, {"ENABLE_THIRD_PARTY_AUTH": False})
    @ddt.data(*THIRD_PARTY_AUTH_PROVIDERS)
    def test_third_party_auth_disabled(self, provider_name):
        response = self.client.get(self.url)
        self.assertNotContains(response, provider_name)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_register_third_party_auth_no_course_id(self, backend_name):
        response = self.client.get(self.url)
        expected_url = _third_party_login_url(backend_name, "register")
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_register_third_party_auth_with_params(self, backend_name):
        params = [
            ('course_id', self.course_id),
            ('enrollment_action', 'enroll'),
            ('course_mode', 'honor'),
            ('email_opt_in', 'true'),
            ('next', '/custom/final/destination'),
        ]
        response = self.client.get(self.url, params)
        expected_url = _third_party_login_url(
            backend_name,
            "register",
            redirect_url=_finish_auth_url(params),
        )
        self.assertContains(response, expected_url)

    @ddt.data(None, "true", "false")
    def test_params(self, opt_in_value):
        params = [
            ('course_id', self.course_id),
            ('enrollment_action', 'enroll'),
            ('course_mode', 'honor'),
            ('email_opt_in', opt_in_value),
            ('next', '/custom/final/destination'),
        ]

        # Get the login page
        response = self.client.get(self.url, params)

        # Verify that the parameters are sent on to the next page correctly
        post_login_handler = _finish_auth_url(params)
        js_success_var = 'var nextUrl = "{}";'.format(post_login_handler)
        self.assertContains(response, js_success_var)

        # Verify that the login link preserves the querystring params
        login_link = u"{url}?{params}".format(
            url=reverse('signin_user'),
            params=urllib.urlencode([('next', post_login_handler)])
        )
        self.assertContains(response, login_link)
