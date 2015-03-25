# -*- coding: utf-8 -*-
""" Tests for student account views. """

import re
from unittest import skipUnless
from urllib import urlencode
import json

import mock
import ddt
import markupsafe
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core import mail
from django.test.utils import override_settings

from util.testing import UrlResetMixin
from third_party_auth.tests.testutil import simulate_running_pipeline
from embargo.test_utils import restrict_course
from openedx.core.djangoapps.user_api.accounts.api import activate_account, create_account
from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import CourseModeFactory


@ddt.ddt
class StudentAccountUpdateTest(UrlResetMixin, TestCase):
    """ Tests for the student account views that update the user's account information. """

    USERNAME = u"heisenberg"
    ALTERNATE_USERNAME = u"walt"
    OLD_PASSWORD = u"ḅḷüëṡḳÿ"
    NEW_PASSWORD = u"🄱🄸🄶🄱🄻🅄🄴"
    OLD_EMAIL = u"walter@graymattertech.com"
    NEW_EMAIL = u"walt@savewalterwhite.com"

    INVALID_ATTEMPTS = 100

    INVALID_EMAILS = [
        None,
        u"",
        u"a",
        "no_domain",
        "no+domain",
        "@",
        "@domain.com",
        "test@no_extension",

        # Long email -- subtract the length of the @domain
        # except for one character (so we exceed the max length limit)
        u"{user}@example.com".format(
            user=(u'e' * (EMAIL_MAX_LENGTH - 11))
        )
    ]

    INVALID_KEY = u"123abc"

    def setUp(self):
        super(StudentAccountUpdateTest, self).setUp("student_account.urls")

        # Create/activate a new account
        activation_key = create_account(self.USERNAME, self.OLD_PASSWORD, self.OLD_EMAIL)
        activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertTrue(result)

    @skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')
    def test_password_change(self):
        # Request a password change while logged in, simulating
        # use of the password reset link from the account page
        response = self._change_password()
        self.assertEqual(response.status_code, 200)

        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Retrieve the activation link from the email body
        email_body = mail.outbox[0].body
        result = re.search('(?P<url>https?://[^\s]+)', email_body)
        self.assertIsNot(result, None)
        activation_link = result.group('url')

        # Visit the activation link
        response = self.client.get(activation_link)
        self.assertEqual(response.status_code, 200)

        # Submit a new password and follow the redirect to the success page
        response = self.client.post(
            activation_link,
            # These keys are from the form on the current password reset confirmation page.
            {'new_password1': self.NEW_PASSWORD, 'new_password2': self.NEW_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your password has been set.")

        # Log the user out to clear session data
        self.client.logout()

        # Verify that the new password can be used to log in
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)

        # Try reusing the activation link to change the password again
        response = self.client.post(
            activation_link,
            {'new_password1': self.OLD_PASSWORD, 'new_password2': self.OLD_PASSWORD},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The password reset link was invalid, possibly because the link has already been used.")

        self.client.logout()

        # Verify that the old password cannot be used to log in
        result = self.client.login(username=self.USERNAME, password=self.OLD_PASSWORD)
        self.assertFalse(result)

        # Verify that the new password continues to be valid
        result = self.client.login(username=self.USERNAME, password=self.NEW_PASSWORD)
        self.assertTrue(result)

    @ddt.data(True, False)
    def test_password_change_logged_out(self, send_email):
        # Log the user out
        self.client.logout()

        # Request a password change while logged out, simulating
        # use of the password reset link from the login page
        if send_email:
            response = self._change_password(email=self.OLD_EMAIL)
            self.assertEqual(response.status_code, 200)
        else:
            # Don't send an email in the POST data, simulating
            # its (potentially accidental) omission in the POST
            # data sent from the login page
            response = self._change_password()
            self.assertEqual(response.status_code, 400)

    def test_password_change_inactive_user(self):
        # Log out the user created during test setup
        self.client.logout()

        # Create a second user, but do not activate it
        create_account(self.ALTERNATE_USERNAME, self.OLD_PASSWORD, self.NEW_EMAIL)

        # Send the view the email address tied to the inactive user
        response = self._change_password(email=self.NEW_EMAIL)

        # Expect that the activation email is still sent,
        # since the user may have lost the original activation email.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

    def test_password_change_no_user(self):
        # Log out the user created during test setup
        self.client.logout()

        # Send the view an email address not tied to any user
        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 400)

    def test_password_change_rate_limited(self):
        # Log out the user created during test setup, to prevent the view from
        # selecting the logged-in user's email address over the email provided
        # in the POST data
        self.client.logout()

        # Make many consecutive bad requests in an attempt to trigger the rate limiter
        for attempt in xrange(self.INVALID_ATTEMPTS):
            self._change_password(email=self.NEW_EMAIL)

        response = self._change_password(email=self.NEW_EMAIL)
        self.assertEqual(response.status_code, 403)

    @ddt.data(
        ('post', 'password_change_request', []),
    )
    @ddt.unpack
    def test_require_http_method(self, correct_method, url_name, args):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - {correct_method}
        url = reverse(url_name, args=args)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    def _change_password(self, email=None):
        """Request to change the user's password. """
        data = {}

        if email:
            data['email'] = email

        return self.client.post(path=reverse('password_change_request'), data=data)


@ddt.ddt
class StudentAccountLoginAndRegistrationTest(UrlResetMixin, ModuleStoreTestCase):
    """ Tests for the student account views that update the user's account information. """

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def setUp(self):
        super(StudentAccountLoginAndRegistrationTest, self).setUp('embargo')

    @ddt.data(
        ("account_login", "login"),
        ("account_register", "register"),
    )
    @ddt.unpack
    def test_login_and_registration_form(self, url_name, initial_mode):
        response = self.client.get(reverse(url_name))
        expected_data = u"data-initial-mode=\"{mode}\"".format(mode=initial_mode)
        self.assertContains(response, expected_data)

    @ddt.data("account_login", "account_register")
    def test_login_and_registration_form_already_authenticated(self, url_name):
        # Create/activate a new account and log in
        activation_key = create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        activate_account(activation_key)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

        # Verify that we're redirected to the dashboard
        response = self.client.get(reverse(url_name))
        self.assertRedirects(response, reverse("dashboard"))

    @ddt.data(
        (False, "account_login"),
        (False, "account_login"),
        (True, "account_login"),
        (True, "account_register"),
    )
    @ddt.unpack
    def test_login_and_registration_form_signin_preserves_params(self, is_edx_domain, url_name):
        params = {
            'enrollment_action': 'enroll',
            'course_id': 'edX/DemoX/Demo_Course'
        }

        # The response should have a "Sign In" button with the URL
        # that preserves the querystring params
        with mock.patch.dict(settings.FEATURES, {'IS_EDX_DOMAIN': is_edx_domain}):
            response = self.client.get(reverse(url_name), params)
        self.assertContains(response, "login?course_id=edX%2FDemoX%2FDemo_Course&enrollment_action=enroll")

        # Add an additional "course mode" parameter
        params['course_mode'] = 'honor'

        # Verify that this parameter is also preserved
        with mock.patch.dict(settings.FEATURES, {'IS_EDX_DOMAIN': is_edx_domain}):
            response = self.client.get(reverse(url_name), params)

        expected_url = (
            "login?course_id=edX%2FDemoX%2FDemo_Course"
            "&enrollment_action=enroll"
            "&course_mode=honor"
        )
        self.assertContains(response, expected_url)

    @mock.patch.dict(settings.FEATURES, {"ENABLE_THIRD_PARTY_AUTH": False})
    @ddt.data("account_login", "account_register")
    def test_third_party_auth_disabled(self, url_name):
        response = self.client.get(reverse(url_name))
        self._assert_third_party_auth_data(response, None, [])

    @ddt.data(
        ("account_login", None, None),
        ("account_register", None, None),
        ("account_login", "google-oauth2", "Google"),
        ("account_register", "google-oauth2", "Google"),
        ("account_login", "facebook", "Facebook"),
        ("account_register", "facebook", "Facebook"),
    )
    @ddt.unpack
    def test_third_party_auth(self, url_name, current_backend, current_provider):
        # Simulate a running pipeline
        if current_backend is not None:
            pipeline_target = "student_account.views.third_party_auth.pipeline"
            with simulate_running_pipeline(pipeline_target, current_backend):
                response = self.client.get(reverse(url_name))

        # Do NOT simulate a running pipeline
        else:
            response = self.client.get(reverse(url_name))

        # This relies on the THIRD_PARTY_AUTH configuration in the test settings
        expected_providers = [
            {
                "name": "Facebook",
                "iconClass": "fa-facebook",
                "loginUrl": self._third_party_login_url("facebook", "login"),
                "registerUrl": self._third_party_login_url("facebook", "register")
            },
            {
                "name": "Google",
                "iconClass": "fa-google-plus",
                "loginUrl": self._third_party_login_url("google-oauth2", "login"),
                "registerUrl": self._third_party_login_url("google-oauth2", "register")
            }
        ]
        self._assert_third_party_auth_data(response, current_provider, expected_providers)

    @ddt.data([], ["honor"], ["honor", "verified", "audit"], ["professional"], ["no-id-professional"])
    def test_third_party_auth_course_id_verified(self, modes):
        # Create a course with the specified course modes
        course = CourseFactory.create()
        for slug in modes:
            CourseModeFactory.create(
                course_id=course.id,
                mode_slug=slug,
                mode_display_name=slug
            )

        # Verify that the entry URL for third party auth
        # contains the course ID and redirects to the track selection page.
        course_modes_choose_url = reverse(
            "course_modes_choose",
            kwargs={"course_id": unicode(course.id)}
        )
        expected_providers = [
            {
                "name": "Facebook",
                "iconClass": "fa-facebook",
                "loginUrl": self._third_party_login_url(
                    "facebook", "login",
                    course_id=unicode(course.id),
                    redirect_url=course_modes_choose_url
                ),
                "registerUrl": self._third_party_login_url(
                    "facebook", "register",
                    course_id=unicode(course.id),
                    redirect_url=course_modes_choose_url
                )
            },
            {
                "name": "Google",
                "iconClass": "fa-google-plus",
                "loginUrl": self._third_party_login_url(
                    "google-oauth2", "login",
                    course_id=unicode(course.id),
                    redirect_url=course_modes_choose_url
                ),
                "registerUrl": self._third_party_login_url(
                    "google-oauth2", "register",
                    course_id=unicode(course.id),
                    redirect_url=course_modes_choose_url
                )
            }
        ]

        # Verify that the login page contains the correct provider URLs
        response = self.client.get(reverse("account_login"), {"course_id": unicode(course.id)})
        self._assert_third_party_auth_data(response, None, expected_providers)

    def test_third_party_auth_course_id_shopping_cart(self):
        # Create a course with a white-label course mode
        course = CourseFactory.create()
        CourseModeFactory.create(
            course_id=course.id,
            mode_slug="honor",
            mode_display_name="Honor",
            min_price=100
        )

        # Verify that the entry URL for third party auth
        # contains the course ID and redirects to the shopping cart
        shoppingcart_url = reverse("shoppingcart.views.show_cart")
        expected_providers = [
            {
                "name": "Facebook",
                "iconClass": "fa-facebook",
                "loginUrl": self._third_party_login_url(
                    "facebook", "login",
                    course_id=unicode(course.id),
                    redirect_url=shoppingcart_url
                ),
                "registerUrl": self._third_party_login_url(
                    "facebook", "register",
                    course_id=unicode(course.id),
                    redirect_url=shoppingcart_url
                )
            },
            {
                "name": "Google",
                "iconClass": "fa-google-plus",
                "loginUrl": self._third_party_login_url(
                    "google-oauth2", "login",
                    course_id=unicode(course.id),
                    redirect_url=shoppingcart_url
                ),
                "registerUrl": self._third_party_login_url(
                    "google-oauth2", "register",
                    course_id=unicode(course.id),
                    redirect_url=shoppingcart_url
                )
            }
        ]

        # Verify that the login page contains the correct provider URLs
        response = self.client.get(reverse("account_login"), {"course_id": unicode(course.id)})
        self._assert_third_party_auth_data(response, None, expected_providers)

    @mock.patch.dict(settings.FEATURES, {'EMBARGO': True})
    def test_third_party_auth_enrollment_embargo(self):
        course = CourseFactory.create()

        # Start the pipeline attempting to enroll in a restricted course
        with restrict_course(course.id) as redirect_url:
            response = self.client.get(reverse("account_login"), {"course_id": unicode(course.id)})

            # Expect that the course ID has been removed from the
            # login URLs (so the user won't be enrolled) and
            # the ?next param sends users to the blocked message.
            expected_providers = [
                {
                    "name": "Facebook",
                    "iconClass": "fa-facebook",
                    "loginUrl": self._third_party_login_url(
                        "facebook", "login",
                        course_id=unicode(course.id),
                        redirect_url=redirect_url
                    ),
                    "registerUrl": self._third_party_login_url(
                        "facebook", "register",
                        course_id=unicode(course.id),
                        redirect_url=redirect_url
                    )
                },
                {
                    "name": "Google",
                    "iconClass": "fa-google-plus",
                    "loginUrl": self._third_party_login_url(
                        "google-oauth2", "login",
                        course_id=unicode(course.id),
                        redirect_url=redirect_url
                    ),
                    "registerUrl": self._third_party_login_url(
                        "google-oauth2", "register",
                        course_id=unicode(course.id),
                        redirect_url=redirect_url
                    )
                }
            ]
            self._assert_third_party_auth_data(response, None, expected_providers)

    @override_settings(SITE_NAME=settings.MICROSITE_TEST_HOSTNAME)
    def test_microsite_uses_old_login_page(self):
        # Retrieve the login page from a microsite domain
        # and verify that we're served the old page.
        resp = self.client.get(
            reverse("account_login"),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME
        )
        self.assertContains(resp, "Log into your Test Microsite Account")
        self.assertContains(resp, "login-form")

    def test_microsite_uses_old_register_page(self):
        # Retrieve the register page from a microsite domain
        # and verify that we're served the old page.
        resp = self.client.get(
            reverse("account_register"),
            HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME
        )
        self.assertContains(resp, "Register for Test Microsite")
        self.assertContains(resp, "register-form")

    def _assert_third_party_auth_data(self, response, current_provider, providers):
        """Verify that third party auth info is rendered correctly in a DOM data attribute. """
        auth_info = markupsafe.escape(
            json.dumps({
                "currentProvider": current_provider,
                "providers": providers
            })
        )

        expected_data = u"data-third-party-auth='{auth_info}'".format(
            auth_info=auth_info
        )
        self.assertContains(response, expected_data)

    def _third_party_login_url(self, backend_name, auth_entry, course_id=None, redirect_url=None):
        """Construct the login URL to start third party authentication. """
        params = [("auth_entry", auth_entry)]
        if redirect_url:
            params.append(("next", redirect_url))
        if course_id:
            params.append(("enroll_course_id", course_id))

        return u"{url}?{params}".format(
            url=reverse("social:begin", kwargs={"backend": backend_name}),
            params=urlencode(params)
        )
