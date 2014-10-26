"""Tests for the login and registration form rendering. """
import urllib
import unittest
from mock import patch
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
import ddt
from django.test.utils import override_settings
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import CourseModeFactory
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase, mixed_store_config
)


# This relies on third party auth being enabled and configured
# in the test settings.  See the setting `THIRD_PARTY_AUTH`
# and the feature flag `ENABLE_THIRD_PARTY_AUTH`
THIRD_PARTY_AUTH_BACKENDS = ["google-oauth2", "facebook"]
THIRD_PARTY_AUTH_PROVIDERS = ["Google", "Facebook"]

# Since we don't need any XML course fixtures, use a modulestore configuration
# that disables the XML modulestore.
MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


def _third_party_login_url(backend_name, auth_entry, course_id=None, redirect_url=None):
    """Construct the login URL to start third party authentication. """
    params = [("auth_entry", auth_entry)]
    if redirect_url:
        params.append(("next", redirect_url))
    if course_id:
        params.append(("enroll_course_id", course_id))

    return u"{url}?{params}".format(
        url=reverse("social:begin", kwargs={"backend": backend_name}),
        params=urllib.urlencode(params)
    )


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class LoginFormTest(ModuleStoreTestCase):
    """Test rendering of the login form. """

    def setUp(self):
        self.url = reverse("signin_user")
        self.course = CourseFactory.create()
        self.course_id = unicode(self.course.id)
        self.course_modes_url = reverse("course_modes_choose", kwargs={"course_id": self.course_id})
        self.courseware_url = reverse("courseware", args=[self.course_id])

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
        response = self.client.get(self.url, {"course_id": self.course_id})

        # Expect that the course ID is added to the third party auth entry
        # point, so that the pipeline will enroll the student and
        # redirect the student to the track selection page.
        expected_url = _third_party_login_url(
            backend_name,
            "login",
            course_id=self.course_id,
            redirect_url=self.course_modes_url
        )
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_third_party_auth_with_white_label_course(self, backend_name):
        # Set the course mode to honor with a min price,
        # indicating that the course is behind a paywall.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug="honor",
            mode_display_name="Honor",
            min_price=100
        )

        # Expect that we're redirected to the shopping cart
        # instead of to the track selection page.
        response = self.client.get(self.url, {"course_id": self.course_id})
        expected_url = _third_party_login_url(
            backend_name,
            "login",
            course_id=self.course_id,
            redirect_url=reverse("shoppingcart.views.show_cart")
        )
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_third_party_auth_with_redirect_url(self, backend_name):
        # Try to access courseware while logged out, expecting to be
        # redirected to the login page.
        response = self.client.get(self.courseware_url, follow=True)
        self.assertRedirects(
            response,
            u"{url}?next={redirect_url}".format(
                url=reverse("accounts_login"),
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


@ddt.ddt
@override_settings(MODULESTORE=MODULESTORE_CONFIG)
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class RegisterFormTest(TestCase):
    """Test rendering of the registration form. """

    def setUp(self):
        self.url = reverse("register_user")
        self.course = CourseFactory.create()
        self.course_id = unicode(self.course.id)
        self.course_modes_url = reverse("course_modes_choose", kwargs={"course_id": self.course_id})

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
    def test_register_third_party_auth_with_course_id(self, backend_name):
        response = self.client.get(self.url, {"course_id": self.course_id})
        expected_url = _third_party_login_url(
            backend_name,
            "register",
            course_id=self.course_id,
            redirect_url=self.course_modes_url
        )
        self.assertContains(response, expected_url)

    @ddt.data(*THIRD_PARTY_AUTH_BACKENDS)
    def test_third_party_auth_with_white_label_course(self, backend_name):
        # Set the course mode to honor with a min price,
        # indicating that the course is behind a paywall.
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug="honor",
            mode_display_name="Honor",
            min_price=100
        )

        # Expect that we're redirected to the shopping cart
        # instead of to the track selection page.
        response = self.client.get(self.url, {"course_id": self.course_id})
        expected_url = _third_party_login_url(
            backend_name,
            "register",
            course_id=self.course_id,
            redirect_url=reverse("shoppingcart.views.show_cart")
        )
        self.assertContains(response, expected_url)
