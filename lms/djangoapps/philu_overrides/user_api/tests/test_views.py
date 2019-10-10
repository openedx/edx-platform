"""Tests for the user API at the HTTP request level. """

import datetime
import json
from unittest import SkipTest, skipUnless

from pytz import UTC

import ddt
import factory
import httpretty
import mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.test.client import RequestFactory
from django.test.testcases import TransactionTestCase
from django.test.utils import override_settings
from lms.djangoapps.onboarding.tests.factories import UserFactory
from lms.djangoapps.philu_overrides.user_api.views import RegistrationViewCustom
from openedx.core.djangoapps.user_api.accounts import (EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH, PASSWORD_MAX_LENGTH,
                                                       PASSWORD_MIN_LENGTH, USERNAME_MAX_LENGTH,
                                                       USERNAME_MIN_LENGTH)
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from openedx.core.djangoapps.user_api.tests.test_constants import SORTED_COUNTRIES
from openedx.core.djangoapps.user_api.tests.test_helpers import TestCaseForm
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.lib.api.test_utils import ApiTestCase
from social.apps.django_app.default.models import UserSocialAuth
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin
from third_party_auth.tests.utils import (ThirdPartyOAuthTestMixin, ThirdPartyOAuthTestMixinFacebook,
                                          ThirdPartyOAuthTestMixinGoogle)

from .utils import mocked_registration_view_post_method, simulate_running_pipeline


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


@override_settings(
    MIDDLEWARE_CLASSES=[
        klass for klass in settings.MIDDLEWARE_CLASSES
        if klass != 'lms.djangoapps.onboarding.middleware.RedirectMiddleware'
    ]
)
@ddt.ddt
@skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class RegistrationViewTest(ThirdPartyAuthTestMixin, ApiTestCase):
    """Tests for the registration version one end-points of the User API. """

    maxDiff = None

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"
    NAME = "Bob Smith"
    FIRSTNAME = "Bob"
    LASTNAME = "Smith"
    EDUCATION = "m"
    YEAR_OF_BIRTH = "1998"
    ADDRESS = "123 Fake Street"
    CITY = "Springfield"
    COUNTRY = "us"
    GOALS = "Learn all the things!"

    def setUp(self):
        super(RegistrationViewTest, self).setUp()
        self.url = reverse("user_api_registration")

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
        raise SkipTest("Django 1.4's test client does not support patch")

    def test_register_form_default_fields(self):
        no_extra_fields_setting = {}

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"email",
                u"type": u"email",
                u"required": True,
                u"label": u"Email",
                u"placeholder": u"username@domain.com",
                u"restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
                u"errorMessages": {
                    u"email": u"The email you entered is not valid. Please provide"
                              u" a valid email in order to create an account."
                }
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"username",
                u"type": u"text",
                u"required": True,
                u"label": u"Public Username",
                u"placeholder": u"Public Username",
                u"instructions": u"The name that will identify you in your courses - <strong>(cannot be changed later)</strong>",
                # pylint: disable=line-too-long
                u"restrictions": {
                    "min_length": USERNAME_MIN_LENGTH,
                    "max_length": USERNAME_MAX_LENGTH
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"placeholder": "Password",
                u"name": u"password",
                u"type": u"password",
                u"required": True,
                u"label": u"Password",
                u"restrictions": {
                    'min_length': PASSWORD_MIN_LENGTH,
                    'max_length': PASSWORD_MAX_LENGTH
                },
            }
        )

    @override_settings(
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm'
    )
    def test_extension_form_fields(self):
        no_extra_fields_setting = {}

        # Verify other fields didn't disappear for some reason.
        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"email",
                u"type": u"email",
                u"required": True,
                u"label": u"Email",
                u"placeholder": u"username@domain.com",
                u"restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
                u"errorMessages": {
                    u"email": u"The email you entered is not valid. Please provide"
                              u" a valid email in order to create an account."
                }
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"favorite_editor",
                u"type": u"select",
                u"required": False,
                u"label": u"Favorite Editor",
                u"placeholder": u"cat",
                u"defaultValue": u"vim",
                u"errorMessages": {
                    u'required': u'This field is required.',
                    u'invalid_choice': u'Select a valid choice. %(value)s is not one of the available choices.',
                }
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"favorite_movie",
                u"type": u"text",
                u"required": True,
                u"label": u"Fav Flick",
                u"placeholder": None,
                u"defaultValue": None,
                u"errorMessages": {
                    u'required': u'Please tell us your favorite movie.',
                    u'invalid': u"We're pretty sure you made that movie up."
                },
                u"restrictions": {
                    "min_length": TestCaseForm.MOVIE_MIN_LEN,
                    "max_length": TestCaseForm.MOVIE_MAX_LEN,
                }
            }
        )

    def test_register_form_third_party_auth_running(self):
        no_extra_fields_setting = {}

        self.configure_google_provider(enabled=True)
        with simulate_running_pipeline(
                "openedx.core.djangoapps.user_api.views.third_party_auth.pipeline",
                "google-oauth2", email="bob@example.com",
                fullname="Bob", username="Bob123"
        ):
            # Password field should be hidden
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"placeholder": "Password",
                    u"name": u"password",
                    u"type": u"password",
                    u"label": u"Password",
                    u"required": True,
                    u"restrictions": {
                        'min_length': PASSWORD_MIN_LENGTH,
                        'max_length': PASSWORD_MAX_LENGTH
                    },
                }
            )

            # Email should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"email",
                    u"defaultValue": u"bob@example.com",
                    u"type": u"email",
                    u"required": True,
                    u"label": u"Email",
                    u"placeholder": u"username@domain.com",
                    u"restrictions": {
                        "min_length": EMAIL_MIN_LENGTH,
                        "max_length": EMAIL_MAX_LENGTH
                    },
                    u"errorMessages": {
                        u"email": u"The email you entered is not valid. Please provide"
                                  u" a valid email in order to create an account."
                    }
                }
            )

            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"first_name",
                    u"defaultValue": u"",
                    u"type": u"text",
                    u"required": True,
                    u"instructions": u"",
                    u"label": u"First Name",
                    u"placeholder": None,
                    u"restrictions": {},
                    u"errorMessages": {u"required": u"Please enter your First Name."}
                }
            )

            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"last_name",
                    u"defaultValue": u"",
                    u"type": u"text",
                    u"required": True,
                    u"instructions": u"",
                    u"label": u"Last Name",
                    u"placeholder": None,
                    u"restrictions": {},
                    u"errorMessages": {u"required": u"Please enter your Last Name."}
                }
            )

            # Username should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"username",
                    u"defaultValue": u"Bob123",
                    u"type": u"text",
                    u"required": True,
                    u"label": u"Public Username",
                    u"placeholder": u"Public Username",
                    u"instructions": u"The name that will identify you in your courses - <strong>(cannot be changed later)</strong>",
                    # pylint: disable=line-too-long
                    u"restrictions": {
                        "min_length": USERNAME_MIN_LENGTH,
                        "max_length": USERNAME_MAX_LENGTH
                    }
                }
            )

    def test_register_form_level_of_education(self):
        self._assert_reg_field(
            {"level_of_education": "optional"},
            {
                "name": "level_of_education",
                "type": "select",
                "required": False,
                "label": "Highest level of education completed",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "p", "name": "Doctorate"},
                    {"value": "m", "name": "Master's or professional degree"},
                    {"value": "b", "name": "Bachelor's degree"},
                    {"value": "a", "name": "Associate degree"},
                    {"value": "hs", "name": "Secondary/high school"},
                    {"value": "jhs", "name": "Junior secondary/junior high/middle school"},
                    {"value": "el", "name": "Elementary/primary school"},
                    {"value": "none", "name": "No formal education"},
                    {"value": "other", "name": "Other education"},
                ],
            }
        )

    @mock.patch('util.enterprise_helpers.active_provider_requests_data_sharing')
    @mock.patch('util.enterprise_helpers.active_provider_enforces_data_sharing')
    @mock.patch('util.enterprise_helpers.get_enterprise_customer_for_request')
    @mock.patch('util.enterprise_helpers.configuration_helpers')
    def test_register_form_consent_field(self, config_helper, get_ec, mock_enforce, mock_request):
        """
        Test that if we have an EnterpriseCustomer active for the request, and that
        EnterpriseCustomer is set to require data sharing consent, the correct
        field is added to the form descriptor.
        """
        fake_ec = mock.MagicMock(
            enforces_data_sharing_consent=mock.MagicMock(return_value=True),
            requests_data_sharing_consent=True,
        )
        fake_ec.name = 'MegaCorp'
        get_ec.return_value = fake_ec
        config_helper.get_value.return_value = 'OpenEdX'
        mock_request.return_value = True
        mock_enforce.return_value = True
        self._assert_reg_field(
            dict(),
            {
                u"name": u"data_sharing_consent",
                u"type": u"checkbox",
                u"required": True,
                u"label": (
                    "I agree to allow OpenEdX to share data about my enrollment, "
                    "completion and performance in all OpenEdX courses and programs "
                    "where my enrollment is sponsored by MegaCorp."
                ),
                u"defaultValue": False,
                u"errorMessages": {
                    u'required': u'To link your account with MegaCorp, you are required to consent to data sharing.',
                }
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.views._')
    def test_register_form_level_of_education_translations(self, fake_gettext):
        fake_gettext.side_effect = lambda text: text + ' TRANSLATED'

        self._assert_reg_field(
            {"level_of_education": "optional"},
            {
                "name": "level_of_education",
                "type": "select",
                "required": False,
                "label": "Highest level of education completed TRANSLATED",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "p", "name": "Doctorate TRANSLATED"},
                    {"value": "m", "name": "Master's or professional degree TRANSLATED"},
                    {"value": "b", "name": "Bachelor's degree TRANSLATED"},
                    {"value": "a", "name": "Associate degree TRANSLATED"},
                    {"value": "hs", "name": "Secondary/high school TRANSLATED"},
                    {"value": "jhs", "name": "Junior secondary/junior high/middle school TRANSLATED"},
                    {"value": "el", "name": "Elementary/primary school TRANSLATED"},
                    {"value": "none", "name": "No formal education TRANSLATED"},
                    {"value": "other", "name": "Other education TRANSLATED"},
                ],
            }
        )

    def test_register_form_gender(self):
        self._assert_reg_field(
            {"gender": "optional"},
            {
                "name": "gender",
                "type": "select",
                "required": False,
                "label": "Gender",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "m", "name": "Male"},
                    {"value": "f", "name": "Female"},
                    {"value": "o", "name": "Other/Prefer Not to Say"},
                ],
            }
        )

    @mock.patch('openedx.core.djangoapps.user_api.views._')
    def test_register_form_gender_translations(self, fake_gettext):
        fake_gettext.side_effect = lambda text: text + ' TRANSLATED'

        self._assert_reg_field(
            {"gender": "optional"},
            {
                "name": "gender",
                "type": "select",
                "required": False,
                "label": "Gender TRANSLATED",
                "options": [
                    {"value": "", "name": "--", "default": True},
                    {"value": "m", "name": "Male TRANSLATED"},
                    {"value": "f", "name": "Female TRANSLATED"},
                    {"value": "o", "name": "Other/Prefer Not to Say TRANSLATED"},
                ],
            }
        )

    def test_register_form_year_of_birth(self):
        this_year = datetime.datetime.now(UTC).year
        year_options = (
            [{"value": "", "name": "--", "default": True}] + [
                {"value": unicode(year), "name": unicode(year)}
                for year in range(this_year, this_year - 120, -1)
            ]
        )
        self._assert_reg_field(
            {"year_of_birth": "optional"},
            {
                "name": "year_of_birth",
                "type": "select",
                "required": False,
                "label": "Year of birth",
                "options": year_options,
            }
        )

    def test_registration_form_mailing_address(self):
        self._assert_reg_field(
            {"mailing_address": "optional"},
            {
                "name": "mailing_address",
                "type": "textarea",
                "required": False,
                "label": "Mailing address",
            }
        )

    def test_registration_form_goals(self):
        self._assert_reg_field(
            {"goals": "optional"},
            {
                "name": "goals",
                "type": "textarea",
                "required": False,
                "label": u"Tell us why you're interested in {platform_name}".format(
                    platform_name=settings.PLATFORM_NAME
                )
            }
        )

    def test_registration_form_city(self):
        self._assert_reg_field(
            {"city": "optional"},
            {
                "name": "city",
                "type": "text",
                "required": False,
                "label": "City",
            }
        )

    def test_registration_form_state(self):
        self._assert_reg_field(
            {"state": "optional"},
            {
                "name": "state",
                "type": "text",
                "required": False,
                "label": "State/Province/Region",
            }
        )

    def test_registration_form_country(self):
        country_options = (
            [{"name": "--", "value": "", "default": True}] +
            [
                {"value": country_code, "name": unicode(country_name)}
                for country_code, country_name in SORTED_COUNTRIES
            ]
        )
        self._assert_reg_field(
            {"country": "required"},
            {
                "label": "Country",
                "name": "country",
                "type": "select",
                "required": True,
                "options": country_options,
                "errorMessages": {
                    "required": "Please select your Country."
                },
            }
        )

    @override_settings(
        MKTG_URLS={"ROOT": "https://www.test.com/", "HONOR": "honor"},
    )
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": True})
    def test_registration_honor_code_mktg_site_enabled(self):
        link_label = 'Terms of Service and Honor Code'
        self._assert_reg_field(
            {"honor_code": "required"},
            {
                "label": u"Check here if you agree to be bound by, and to comply with, our ",
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": "Please accept our Terms and Conditions by checking the Terms and Conditions"
                                " checkbox before creating an account."
                }
            }
        )

    @override_settings(MKTG_URLS_LINK_MAP={"HONOR": "honor"})
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": False})
    def test_registration_honor_code_mktg_site_disabled(self):
        link_label = 'Terms of Service and Honor Code'
        self._assert_reg_field(
            {"honor_code": "required"},
            {
                "label": u"Check here if you agree to be bound by, and to comply with, our ",
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": "Please accept our Terms and Conditions by checking the Terms and Conditions"
                                " checkbox before creating an account."
                }
            }
        )

    @override_settings(MKTG_URLS={
        "ROOT": "https://www.test.com/",
        "HONOR": "honor",
        "TOS": "tos",
    })
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": True})
    def test_registration_separate_terms_of_service_mktg_site_enabled(self):
        # Honor code field should say ONLY honor code,
        # not "terms of service and honor code"
        link_label = 'Honor Code'
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"Check here if you agree to be bound by, and to comply with, our ",
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": "Please accept our Terms and Conditions by checking the Terms and Conditions"
                                " checkbox before creating an account."
                }
            }
        )

        # Terms of service field should also be present
        link_label = 'Terms of Service'
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_label
                ),
                "name": "terms_of_service",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
                }
            }
        )

    @override_settings(MKTG_URLS_LINK_MAP={"HONOR": "honor", "TOS": "tos"})
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": False})
    def test_registration_separate_terms_of_service_mktg_site_disabled(self):
        # Honor code field should say ONLY honor code,
        # not "terms of service and honor code"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"Check here if you agree to be bound by, and to comply with, our ",
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": "Please accept our Terms and Conditions by checking the Terms and Conditions"
                                " checkbox before creating an account."
                }
            }
        )

        # Terms of service field should also be present
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} Terms of Service".format(
                    platform_name=settings.PLATFORM_NAME
                ),
                "name": "terms_of_service",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} Terms of Service".format(
                        # pylint: disable=line-too-long
                        platform_name=settings.PLATFORM_NAME
                    )
                }
            }
        )

    @override_settings(
        REGISTRATION_EXTRA_FIELDS={
            "level_of_education": "optional",
            "gender": "optional",
            "year_of_birth": "optional",
            "mailing_address": "optional",
            "goals": "optional",
            "city": "optional",
            "state": "optional",
            "country": "required",
            "honor_code": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
    )
    def test_field_order(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content)
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            u"email",
            u"username",
            u"password",
            u"favorite_movie",
            u"favorite_editor",
            u"city",
            u"state",
            u"country",
            u"gender",
            u"year_of_birth",
            u"level_of_education",
            u"mailing_address",
            u"goals",
            u"honor_code"
        ])

    @factory.django.mute_signals(post_save)
    def test_register(self):
        # Create a new registration
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertHttpOK(response)
        self.assertIn(settings.EDXMKTG_LOGGED_IN_COOKIE_NAME, self.client.cookies)
        self.assertIn(settings.EDXMKTG_USER_INFO_COOKIE_NAME, self.client.cookies)

        user = User.objects.get(username=self.USERNAME)
        request = RequestFactory().get('/url')
        request.user = user
        account_settings = get_account_settings(request)[0]

        self.assertEqual(self.USERNAME, account_settings["username"])
        self.assertEqual(self.EMAIL, account_settings["email"])
        self.assertFalse(account_settings["is_active"])
        self.assertEqual(self.NAME, account_settings["name"])

        # Verify that we've been logged in
        # by trying to access a page that requires authentication
        response = self.client.get(reverse("learner_profile", kwargs={'username': self.USERNAME}))
        self.assertHttpOK(response)

    @override_settings(REGISTRATION_EXTRA_FIELDS={
        "level_of_education": "optional",
        "gender": "optional",
        "year_of_birth": "optional",
        "mailing_address": "optional",
        "goals": "optional",
        "country": "required",
    })
    @factory.django.mute_signals(post_save)
    def test_register_with_profile_info(self):
        # Register, providing lots of demographic info
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "level_of_education": self.EDUCATION,
            "mailing_address": self.ADDRESS,
            "year_of_birth": self.YEAR_OF_BIRTH,
            "goals": self.GOALS,
            "country": self.COUNTRY,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertHttpOK(response)

        # Verify the user's account
        user = User.objects.get(username=self.USERNAME)
        request = RequestFactory().get('/url')
        request.user = user
        account_settings = get_account_settings(request)[0]

        self.assertEqual(account_settings["level_of_education"], self.EDUCATION)
        self.assertEqual(account_settings["mailing_address"], self.ADDRESS)
        self.assertEqual(account_settings["year_of_birth"], int(self.YEAR_OF_BIRTH))
        self.assertEqual(account_settings["goals"], self.GOALS)
        self.assertEqual(account_settings["country"], self.COUNTRY)

    @mock.patch('mailchimp_pipeline.signals.handlers.task_send_account_activation_email')
    @factory.django.mute_signals(post_save)
    def test_activation_email(self, mock_func):
        # Register, which should trigger an activation email
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertHttpOK(response)

        # Verify that the activation email was sent
        mock_func.assert_called_once()

    @ddt.data(
        {"email": ""},
        {"email": "invalid"},
        {"first_name": ""},
        {"last_name": ""},
        {"username": ""},
        {"username": "a"},
        {"password": ""},
    )
    def test_register_invalid_input(self, invalid_fields):
        # Initially, the field values are all valid
        data = {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        }
        # Override the valid fields, making the input invalid
        data.update(invalid_fields)

        # Attempt to create the account, expecting an error response
        response = self.client.post(self.url, data)
        self.assertHttpBadRequest(response)

    @override_settings(REGISTRATION_EXTRA_FIELDS={"country": "required"})
    @ddt.data("email", "username", "password", "country", ("first_name", "last_name"))
    def test_register_missing_required_field(self, missing_field):
        data = {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "country": self.COUNTRY,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        }

        if isinstance(missing_field, tuple):
            for key in missing_field:
                del data[key]
        else:
            del data[missing_field]

        # Send a request missing a field
        response = self.client.post(self.url, data)
        self.assertHttpBadRequest(response)

    def test_register_duplicate_email(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""

        })
        self.assertHttpOK(response)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""

        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    def test_register_duplicate_username(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""

        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": "someone+else@example.com",
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "username": [{
                    "user_message": "The username you entered is already being used. Please enter another username."
                }]
            }
        )

    def test_register_duplicate_username_and_email(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "username": [{
                    "user_message": "The username you entered is already being used. Please enter another username."
                }],
                "email": [{
                    "user_message": (
                        "It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    @override_settings(REGISTRATION_EXTRA_FIELDS={"honor_code": "hidden", "terms_of_service": "hidden"})
    def test_register_hidden_honor_code_and_terms_of_service(self):
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""
        })
        self.assertHttpOK(response)

    def test_missing_fields(self):
        response = self.client.post(
            self.url,
            {
                "email": self.EMAIL,
                "name": self.NAME,
                "honor_code": "true",
                "first_name": self.FIRSTNAME,
                "last_name": self.LASTNAME,
                "confirm_password": self.PASSWORD,
                "is_poc": 1,
                "partners_opt_in": ""
            }
        )
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json,
            {
                "username": [{"user_message": "Username must be minimum of two characters long"}],
                "password": [{"user_message": "A valid password is required"}],
            }
        )

    def _assert_reg_field(self, extra_fields_setting, expected_field):
        """Retrieve the registration form description from the server and
        verify that it contains the expected field.

        Args:
            extra_fields_setting (dict): Override the Django setting controlling
                which extra fields are displayed in the form.

            expected_field (dict): The field definition we expect to find in the form.

        Raises:
            AssertionError

        """
        # Add in fields that are always present

        defaults = [
            ("label", ""),
            ("instructions", ""),
            ("placeholder", ""),
            ("defaultValue", ""),
            ("restrictions", {}),
            ("errorMessages", {}),
        ]
        for key, value in defaults:
            if key not in expected_field:
                expected_field[key] = value

        # Retrieve the registration form description
        with override_settings(REGISTRATION_EXTRA_FIELDS=extra_fields_setting):
            response = self.client.get(self.url)
            self.assertHttpOK(response)

        # Verify that the form description matches what we'd expect
        form_desc = json.loads(response.content)

        # Search the form for this field
        actual_field = None
        for field in form_desc["fields"]:
            if field["name"] == expected_field["name"]:
                actual_field = field
                break

        self.assertIsNot(
            actual_field, None,
            msg="Could not find field {name}".format(name=expected_field["name"])
        )

        for key, value in expected_field.iteritems():
            self.assertEqual(
                expected_field[key], actual_field[key],
                msg=u"Expected {expected} for {key} but got {actual} instead".format(
                    key=key,
                    expected=expected_field[key],
                    actual=actual_field[key]
                )
            )

    def test_country_overrides(self):
        """Test that overridden countries are available in country list."""
        # Retrieve the registration form description
        with override_settings(REGISTRATION_EXTRA_FIELDS={"country": "required"}):
            response = self.client.get(self.url)
            self.assertHttpOK(response)

        self.assertContains(response, 'Kosovo')

    @mock.patch.object(RegistrationViewCustom, 'post', mocked_registration_view_post_method)
    def test_registration_post_request_conflicts(self):
        """ To check conflicts without doing doing any extra checks using mocked method """
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""

        })

        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "first_name": self.FIRSTNAME,
            "last_name": self.LASTNAME,
            "confirm_password": self.PASSWORD,
            "is_poc": 1,
            "partners_opt_in": ""

        })


class RegistrationViewTestV2(RegistrationViewTest):
    """Tests for the registration version two end-points of the User API. """

    def setUp(self):
        super(RegistrationViewTestV2, self).setUp()
        self.url = reverse("user_api_registration_v2")

    @override_settings(
        REGISTRATION_EXTRA_FIELDS={
            "level_of_education": "optional",
            "gender": "optional",
            "year_of_birth": "optional",
            "mailing_address": "optional",
            "goals": "optional",
            "city": "optional",
            "state": "optional",
            "country": "required",
            "honor_code": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
    )
    def test_field_order(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content)
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            u"email",
            u"username",
            u"password",
            u"confirm_password",
            u"first_name",
            u"last_name",
            u"opt_in",
            u"city",
            u"state",
            u"country",
            u"gender",
            u"year_of_birth",
            u"level_of_education",
            u"mailing_address",
            u"goals",
            u"honor_code"
        ])

    def test_extension_form_fields(self):
        raise SkipTest("RegisterationView Version 2 doesn't support this test")
