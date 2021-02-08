"""Tests for the user API at the HTTP request level. """

import json
from unittest import skipUnless


import ddt
import factory
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.core.djangoapps.user_api.accounts import (EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH, PASSWORD_MAX_LENGTH,
                                                       PASSWORD_MIN_LENGTH)
from openedx.core.lib.api.test_utils import ApiTestCase


@ddt.ddt
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class LoginSessionViewTest(ApiTestCase):
    """Tests for the login end-points of the user API. """

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"

    def setUp(self):
        super(LoginSessionViewTest, self).setUp()
        self.url = reverse("user_api_login_session")

    @ddt.data("get", "post")
    def test_auth_disabled(self, method):
        self.assertAuthDisabled(method, self.url)

    def test_allowed_methods(self):
        self.assertAllowedMethods(self.url, ["GET", "POST", "HEAD", "OPTIONS"])

    def test_put_not_allowed(self):
        response = self.client.put(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_patch_not_allowed(self):
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_login_form(self):
        # Retrieve the login form
        response = self.client.get(self.url, content_type="application/json")
        self.assertHttpOK(response)

        # Verify that the form description matches what we expect
        form_desc = json.loads(response.content)
        self.assertEqual(form_desc["method"], "post")
        self.assertEqual(form_desc["submit_url"], self.url)
        self.assertItemsEqual(form_desc["fields"], [
            {
                "name": "email",
                "defaultValue": "",
                "type": "email",
                "required": True,
                "label": "Email",
                "placeholder": "username@domain.com",
                "instructions": u"The email address you used to register with {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                "restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            },
            {
                "name": "password",
                "defaultValue": "",
                "type": "password",
                "required": True,
                "label": "Password",
                "placeholder": "",
                "instructions": "",
                "restrictions": {
                    "min_length": PASSWORD_MIN_LENGTH,
                    "max_length": PASSWORD_MAX_LENGTH
                },
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            },
            {
                "name": "remember",
                "defaultValue": False,
                "type": "checkbox",
                "required": False,
                "label": "Remember my login credentials so I don't need to fill up these fields every time I log in.",
                "placeholder": "",
                "instructions": "",
                "restrictions": {},
                "errorMessages": {},
                "supplementalText": "",
                "supplementalLink": "",
            },
        ])

    @factory.django.mute_signals(post_save)
    def test_login(self):
        # Create a test user
        user = UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Login
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "password": self.PASSWORD,
        })
        self.assertHttpOK(response)

        user.profile.level_of_education = 'BD'
        user.extended_profile.english_proficiency = 'ADV'
        user.profile.save()
        user.extended_profile.save()

        # Verify that we logged in successfully by accessing
        # a page that requires authentication.
        response = self.client.get(reverse("learner_profile", kwargs={'username': user.username}))
        self.assertHttpOK(response)

    @ddt.data(
        ('true', False),
        ('false', True),
        (None, True),
    )
    @ddt.unpack
    @factory.django.mute_signals(post_save)
    def test_login_remember_me(self, remember_value, expire_at_browser_close):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Login and remember me
        data = {
            "email": self.EMAIL,
            "password": self.PASSWORD,
        }

        if remember_value is not None:
            data["remember"] = remember_value

        response = self.client.post(self.url, data)
        self.assertHttpOK(response)

        # Verify that the session expiration was set correctly
        self.assertEqual(
            self.client.session.get_expire_at_browser_close(),
            expire_at_browser_close
        )

    @factory.django.mute_signals(post_save)
    def test_invalid_credentials(self):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Invalid password
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "password": "invalid"
        })
        self.assertHttpForbidden(response)

        # Invalid email address
        response = self.client.post(self.url, {
            "email": "invalid@example.com",
            "password": self.PASSWORD,
        })
        self.assertHttpForbidden(response)

    @factory.django.mute_signals(post_save)
    def test_missing_login_params(self):
        # Create a test user
        UserFactory.create(username=self.USERNAME, email=self.EMAIL, password=self.PASSWORD)

        # Missing password
        response = self.client.post(self.url, {
            "email": self.EMAIL,
        })
        self.assertHttpBadRequest(response)

        # Missing email
        response = self.client.post(self.url, {
            "password": self.PASSWORD,
        })
        self.assertHttpBadRequest(response)

        # Missing both email and password
        response = self.client.post(self.url, {})
        self.assertHttpBadRequest(response)
