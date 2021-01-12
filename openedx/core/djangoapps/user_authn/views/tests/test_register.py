# -*- coding: utf-8 -*-
"""Tests for account creation"""

import json
from datetime import datetime
from unittest import skipIf, skipUnless

import ddt
import httpretty
import mock
import six
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import TransactionTestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from pytz import UTC
from six.moves import range
from social_django.models import Partial, UserSocialAuth

from edx_toggles.toggles.testutils import override_waffle_flag
from openedx.core.djangoapps.site_configuration.helpers import get_value
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from openedx.core.djangoapps.user_api.accounts import (
    EMAIL_BAD_LENGTH_MSG,
    EMAIL_CONFLICT_MSG,
    EMAIL_INVALID_MSG,
    EMAIL_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
    NAME_MAX_LENGTH,
    REQUIRED_FIELD_CONFIRM_EMAIL_MSG,
    USERNAME_BAD_LENGTH_MSG,
    USERNAME_CONFLICT_MSG,
    USERNAME_INVALID_CHARS_ASCII,
    USERNAME_INVALID_CHARS_UNICODE,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH
)
from openedx.core.djangoapps.user_api.accounts.api import get_account_settings
from openedx.core.djangoapps.user_api.accounts.tests import testutils
from openedx.core.djangoapps.user_api.accounts.tests.retirement_helpers import (  # pylint: disable=unused-import
    RetirementTestCase,
    fake_requested_retirement,
    setup_retirement_states
)
from openedx.core.djangoapps.user_api.tests.test_constants import SORTED_COUNTRIES
from openedx.core.djangoapps.user_api.tests.test_helpers import TestCaseForm
from openedx.core.djangoapps.user_api.tests.test_views import UserAPITestCase
from openedx.core.djangoapps.user_authn.views.register import REGISTRATION_FAILURE_LOGGING_FLAG
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_lms
from openedx.core.lib.api import test_utils
from common.djangoapps.student.helpers import authenticate_new_user
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.third_party_auth.tests.testutil import ThirdPartyAuthTestMixin, simulate_running_pipeline
from common.djangoapps.third_party_auth.tests.utils import (
    ThirdPartyOAuthTestMixin,
    ThirdPartyOAuthTestMixinFacebook,
    ThirdPartyOAuthTestMixinGoogle
)
from common.djangoapps.util.password_policy_validators import (
    DEFAULT_MAX_PASSWORD_LENGTH,
    create_validator_config,
    password_validators_instruction_texts,
    password_validators_restrictions
)


@ddt.ddt
@skip_unless_lms
class RegistrationViewValidationErrorTest(ThirdPartyAuthTestMixin, UserAPITestCase, RetirementTestCase):
    """
    Tests for catching duplicate email and username validation errors within
    the registration end-points of the User API.
    """

    maxDiff = None

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"
    NAME = "Bob Smith"
    EDUCATION = "m"
    YEAR_OF_BIRTH = "1998"
    ADDRESS = "123 Fake Street"
    CITY = "Springfield"
    COUNTRY = "us"
    GOALS = "Learn all the things!"

    def setUp(self):  # pylint: disable=arguments-differ
        super(RegistrationViewValidationErrorTest, self).setUp()
        self.url = reverse("user_api_registration")

    def test_register_retired_email_validation_error(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Initiate retirement for the above user:
        fake_requested_retirement(User.objects.get(username=self.USERNAME))

        # Try to create a second user with the same email address as the retired user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    def test_register_duplicate_retired_username_account_validation_error(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Initiate retirement for the above user.
        fake_requested_retirement(User.objects.get(username=self.USERNAME))

        with mock.patch('openedx.core.djangoapps.user_authn.views.register.do_create_account') as dummy_do_create_acct:
            # do_create_account should *not* be called - the duplicate retired username
            # should be detected before account creation is called.
            dummy_do_create_acct.side_effect = Exception('do_create_account should *not* have been called!')
            # Try to create a second user with the same username.
            response = self.client.post(self.url, {
                "email": "someone+else@example.com",
                "name": "Someone Else",
                "username": self.USERNAME,
                "password": self.PASSWORD,
                "honor_code": "true",
            })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
                }]
            }
        )

    def test_register_duplicate_email_validation_error(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    @override_waffle_flag(REGISTRATION_FAILURE_LOGGING_FLAG, True)
    def test_registration_failure_logging(self):
        # Register a user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )

    def test_register_duplicate_username_account_validation_error(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": "someone+else@example.com",
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
                }]
            }
        )

    def test_register_duplicate_username_and_email_validation_errors(self):
        # Register the first user
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username and email
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
                }],
                "email": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different email address."
                    ).format(
                        self.EMAIL
                    )
                }]
            }
        )


@ddt.ddt
@skip_unless_lms
class RegistrationViewTestV1(ThirdPartyAuthTestMixin, UserAPITestCase):
    """Tests for the registration end-points of the User API. """

    maxDiff = None

    USERNAME = "bob"
    EMAIL = "bob@example.com"
    PASSWORD = "password"
    NAME = "Bob Smith"
    EDUCATION = "m"
    YEAR_OF_BIRTH = "1998"
    ADDRESS = "123 Fake Street"
    CITY = "Springfield"
    COUNTRY = "US"
    GOALS = "Learn all the things!"
    PROFESSION_OPTIONS = [
        {
            "name": u'--',
            "value": u'',
            "default": True

        },
        {
            "value": u'software engineer',
            "name": u'Software Engineer',
            "default": False
        },
        {
            "value": u'teacher',
            "name": u'Teacher',
            "default": False
        },
        {
            "value": u'other',
            "name": u'Other',
            "default": False
        }
    ]
    SPECIALTY_OPTIONS = [
        {
            "name": u'--',
            "value": u'',
            "default": True

        },
        {
            "value": "aerospace",
            "name": "Aerospace",
            "default": False
        },
        {
            "value": u'early education',
            "name": u'Early Education',
            "default": False
        },
        {
            "value": u'n/a',
            "name": u'N/A',
            "default": False
        }
    ]
    link_template = u"<a href='/honor' rel='noopener' target='_blank'>{link_label}</a>"

    def setUp(self):  # pylint: disable=arguments-differ
        super(RegistrationViewTestV1, self).setUp()
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
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_register_form_default_fields(self):
        no_extra_fields_setting = {}

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"email",
                u"type": u"email",
                u"required": True,
                u"label": u"Email",
                u"instructions": u"This is what you will use to login.",
                u"restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"name",
                u"type": u"text",
                u"required": True,
                u"label": u"Full Name",
                u"instructions": u"This name will be used on any certificates that you earn.",
                u"restrictions": {
                    "max_length": 255
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"name": u"username",
                u"type": u"text",
                u"required": True,
                u"label": u"Public Username",
                u"instructions": u"The name that will identify you in your courses. "
                                 u"It cannot be changed later.",
                u"restrictions": {
                    "min_length": USERNAME_MIN_LENGTH,
                    "max_length": USERNAME_MAX_LENGTH
                },
            }
        )

        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u"placeholder": "",
                u"name": u"password",
                u"type": u"password",
                u"required": True,
                u"label": u"Password",
                u"instructions": password_validators_instruction_texts(),
                u"restrictions": password_validators_restrictions(),
            }
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config(
            'common.djangoapps.util.password_policy_validators.MinimumLengthValidator', {'min_length': 2}
        ),
        create_validator_config(
            'common.djangoapps.util.password_policy_validators.UppercaseValidator', {'min_upper': 3}
        ),
        create_validator_config(
            'common.djangoapps.util.password_policy_validators.SymbolValidator', {'min_symbol': 1}
        ),
    ])
    def test_register_form_password_complexity(self):
        no_extra_fields_setting = {}

        # Without enabling password policy
        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u'name': u'password',
                u'label': u'Password',
                u"instructions": password_validators_instruction_texts(),
                u"restrictions": password_validators_restrictions(),
            }
        )

        msg = u'Your password must contain at least 2 characters, including ' \
              u'3 uppercase letters & 1 symbol.'
        self._assert_reg_field(
            no_extra_fields_setting,
            {
                u'name': u'password',
                u'label': u'Password',
                u'instructions': msg,
                u"restrictions": password_validators_restrictions(),
            }
        )

    @override_settings(REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm')
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
                u"instructions": u"This is what you will use to login.",
                u"restrictions": {
                    "min_length": EMAIL_MIN_LENGTH,
                    "max_length": EMAIL_MAX_LENGTH
                },
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

    @ddt.data(
        ('pk', 'PK', 'Bob123', 'Bob123'),
        ('Pk', 'PK', None, ''),
        ('pK', 'PK', 'Bob123@edx.org', 'Bob123_edx_org'),
        ('PK', 'PK', 'Bob123123123123123123123123123123123123', 'Bob123123123123123123123123123'),
        ('us', 'US', 'Bob-1231231&23123+1231(2312312312@3123123123', 'Bob-1231231_23123_1231_2312312'),
    )
    @ddt.unpack
    def test_register_form_third_party_auth_running_google(
            self,
            input_country_code,
            expected_country_code,
            input_username,
            expected_username):
        no_extra_fields_setting = {}
        country_options = (
            [
                {
                    "name": "--",
                    "value": "",
                    "default": False
                }
            ] + [
                {
                    "value": country_code,
                    "name": six.text_type(country_name),
                    "default": True if country_code == expected_country_code else False
                }
                for country_code, country_name in SORTED_COUNTRIES
            ]
        )

        provider = self.configure_google_provider(enabled=True)
        with simulate_running_pipeline(
            "openedx.core.djangoapps.user_authn.views.login_form.third_party_auth.pipeline", "google-oauth2",
            email="bob@example.com",
            fullname="Bob",
            username=input_username,
            country=input_country_code
        ):
            self._assert_password_field_hidden(no_extra_fields_setting)
            self._assert_social_auth_provider_present(no_extra_fields_setting, provider)

            # Email should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"email",
                    u"defaultValue": u"bob@example.com",
                    u"type": u"email",
                    u"required": True,
                    u"label": u"Email",
                    u"instructions": u"This is what you will use to login.",
                    u"restrictions": {
                        "min_length": EMAIL_MIN_LENGTH,
                        "max_length": EMAIL_MAX_LENGTH
                    },
                }
            )

            # Full Name should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"name",
                    u"defaultValue": u"Bob",
                    u"type": u"text",
                    u"required": True,
                    u"label": u"Full Name",
                    u"instructions": u"This name will be used on any certificates that you earn.",
                    u"restrictions": {
                        "max_length": NAME_MAX_LENGTH,
                    }
                }
            )

            # Username should be filled in
            self._assert_reg_field(
                no_extra_fields_setting,
                {
                    u"name": u"username",
                    u"defaultValue": expected_username,
                    u"type": u"text",
                    u"required": True,
                    u"label": u"Public Username",
                    u"instructions": u"The name that will identify you in your courses. "
                                     u"It cannot be changed later.",
                    u"restrictions": {
                        "min_length": USERNAME_MIN_LENGTH,
                        "max_length": USERNAME_MAX_LENGTH
                    }
                }
            )

            # Country should be filled in.
            self._assert_reg_field(
                {u"country": u"required"},
                {
                    u"label": u"Country or Region of Residence",
                    u"name": u"country",
                    u"defaultValue": expected_country_code,
                    u"type": u"select",
                    u"required": True,
                    u"options": country_options,
                    u"instructions": u"The country or region where you live.",
                    u"errorMessages": {
                        u"required": u"Select your country or region of residence."
                    },
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
                    {"value": "p", "name": "Doctorate", "default": False},
                    {"value": "m", "name": "Master's or professional degree", "default": False},
                    {"value": "b", "name": "Bachelor's degree", "default": False},
                    {"value": "a", "name": "Associate degree", "default": False},
                    {"value": "hs", "name": "Secondary/high school", "default": False},
                    {"value": "jhs", "name": "Junior secondary/junior high/middle school", "default": False},
                    {"value": "el", "name": "Elementary/primary school", "default": False},
                    {"value": "none", "name": "No formal education", "default": False},
                    {"value": "other", "name": "Other education", "default": False},
                ],
                "errorMessages": {
                    "required": "Select the highest level of education you have completed."
                }
            }
        )

    @mock.patch('openedx.core.djangoapps.user_authn.views.registration_form._')
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
                    {"value": "p", "name": "Doctorate TRANSLATED", "default": False},
                    {"value": "m", "name": "Master's or professional degree TRANSLATED", "default": False},
                    {"value": "b", "name": "Bachelor's degree TRANSLATED", "default": False},
                    {"value": "a", "name": "Associate degree TRANSLATED", "default": False},
                    {"value": "hs", "name": "Secondary/high school TRANSLATED", "default": False},
                    {"value": "jhs", "name": "Junior secondary/junior high/middle school TRANSLATED", "default": False},
                    {"value": "el", "name": "Elementary/primary school TRANSLATED", "default": False},
                    {"value": "none", "name": "No formal education TRANSLATED", "default": False},
                    {"value": "other", "name": "Other education TRANSLATED", "default": False},
                ],
                "errorMessages": {
                    "required": "Select the highest level of education you have completed."
                }
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
                    {"value": "m", "name": "Male", "default": False},
                    {"value": "f", "name": "Female", "default": False},
                    {"value": "o", "name": "Other/Prefer Not to Say", "default": False},
                ],
            }
        )

    @mock.patch('openedx.core.djangoapps.user_authn.views.registration_form._')
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
                    {"value": "m", "name": "Male TRANSLATED", "default": False},
                    {"value": "f", "name": "Female TRANSLATED", "default": False},
                    {"value": "o", "name": "Other/Prefer Not to Say TRANSLATED", "default": False},
                ],
            }
        )

    def test_register_form_year_of_birth(self):
        this_year = datetime.now(UTC).year
        year_options = (
            [
                {
                    "value": "",
                    "name": "--",
                    "default": True
                }
            ] + [
                {
                    "value": six.text_type(year),
                    "name": six.text_type(year),
                    "default": False
                }
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

    def test_register_form_profession_without_profession_options(self):
        self._assert_reg_field(
            {"profession": "required"},
            {
                "name": "profession",
                "type": "text",
                "required": True,
                "label": "Profession",
                "errorMessages": {
                    "required": "Enter your profession."
                }
            }
        )

    @with_site_configuration(
        configuration={
            "EXTRA_FIELD_OPTIONS": {"profession": ["Software Engineer", "Teacher", "Other"]}
        }
    )
    def test_register_form_profession_with_profession_options(self):
        self._assert_reg_field(
            {"profession": "required"},
            {
                "name": "profession",
                "type": "select",
                "required": True,
                "label": "Profession",
                "options": self.PROFESSION_OPTIONS,
                "errorMessages": {
                    "required": "Select your profession."
                },
            }
        )

    def test_register_form_specialty_without_specialty_options(self):
        self._assert_reg_field(
            {"specialty": "required"},
            {
                "name": "specialty",
                "type": "text",
                "required": True,
                "label": "Specialty",
                "errorMessages": {
                    "required": "Enter your specialty."
                }
            }
        )

    @with_site_configuration(
        configuration={
            "EXTRA_FIELD_OPTIONS": {"specialty": ["Aerospace", "Early Education", "N/A"]}
        }
    )
    def test_register_form_specialty_with_specialty_options(self):
        self._assert_reg_field(
            {"specialty": "required"},
            {
                "name": "specialty",
                "type": "select",
                "required": True,
                "label": "Specialty",
                "options": self.SPECIALTY_OPTIONS,
                "errorMessages": {
                    "required": "Select your specialty."
                },
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
                "errorMessages": {
                    "required": "Enter your mailing address."
                }
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
                ),
                "errorMessages": {
                    "required": "Tell us your goals."
                }
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
                "errorMessages": {
                    "required": "Enter your city."
                }
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
            [
                {
                    "name": "--",
                    "value": "",
                    "default": True
                }
            ] + [
                {
                    "value": country_code,
                    "name": six.text_type(country_name),
                    "default": False
                }
                for country_code, country_name in SORTED_COUNTRIES
            ]
        )
        self._assert_reg_field(
            {"country": "required"},
            {
                "label": "Country or Region of Residence",
                "name": "country",
                "type": "select",
                "instructions": "The country or region where you live.",
                "required": True,
                "options": country_options,
                "errorMessages": {
                    "required": "Select your country or region of residence."
                },
            }
        )

    def test_registration_form_confirm_email(self):
        pass

    @override_settings(
        MKTG_URLS={"ROOT": "https://www.test.com/", "HONOR": "honor"},
    )
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": True})
    def test_registration_honor_code_mktg_site_enabled(self):
        link_template = "<a href='https://www.test.com/honor' rel='noopener' target='_blank'>{link_label}</a>"
        link_template2 = u"<a href='#' rel='noopener' target='_blank'>{link_label}</a>"
        link_label = "Terms of Service and Honor Code"
        link_label2 = "Privacy Policy"
        self._assert_reg_field(
            {"honor_code": "required"},
            {
                "label": (u"By creating an account, you agree to the {spacing}"
                          u"{link_label} {spacing}"
                          u"and you acknowledge that {platform_name} and each Member process your "
                          u"personal data in accordance {spacing}"
                          u"with the {link_label2}.").format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label),
                    link_label2=link_template2.format(link_label=link_label2),
                    spacing=' ' * 18
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "plaintext",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
                }
            }
        )

    @override_settings(MKTG_URLS_LINK_MAP={"HONOR": "honor"})
    @mock.patch.dict(settings.FEATURES, {"ENABLE_MKTG_SITE": False})
    def test_registration_honor_code_mktg_site_disabled(self):
        link_template = "<a href='/privacy' rel='noopener' target='_blank'>{link_label}</a>"
        link_label = "Terms of Service and Honor Code"
        link_label2 = "Privacy Policy"
        self._assert_reg_field(
            {"honor_code": "required"},
            {
                "label": (u"By creating an account, you agree to the {spacing}"
                          u"{link_label} {spacing}"
                          u"and you acknowledge that {platform_name} and each Member process your "
                          u"personal data in accordance {spacing}"
                          u"with the {link_label2}.").format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=self.link_template.format(link_label=link_label),
                    link_label2=link_template.format(link_label=link_label2),
                    spacing=' ' * 18
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "plaintext",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} {link_label}".format(
                        platform_name=settings.PLATFORM_NAME,
                        link_label=link_label
                    )
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
        link_template = u"<a href='https://www.test.com/honor' rel='noopener' target='_blank'>{link_label}</a>"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label)
                ),
                "name": "honor_code",
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

        # Terms of service field should also be present
        link_label = "Terms of Service"
        link_template = u"<a href='https://www.test.com/tos' rel='noopener' target='_blank'>{link_label}</a>"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label)
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
        link_label = 'Honor Code'
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=self.link_template.format(link_label=link_label)
                ),
                "name": "honor_code",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} Honor Code".format(
                        platform_name=settings.PLATFORM_NAME
                    )
                }
            }
        )

        link_label = 'Terms of Service'
        # Terms of service field should also be present
        link_template = u"<a href='/tos' rel='noopener' target='_blank'>{link_label}</a>"
        self._assert_reg_field(
            {"honor_code": "required", "terms_of_service": "required"},
            {
                "label": u"I agree to the {platform_name} {link_label}".format(
                    platform_name=settings.PLATFORM_NAME,
                    link_label=link_template.format(link_label=link_label)
                ),
                "name": "terms_of_service",
                "defaultValue": False,
                "type": "checkbox",
                "required": True,
                "errorMessages": {
                    "required": u"You must agree to the {platform_name} Terms of Service".format(
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
            "confirm_email": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
    )
    def test_field_order(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content.decode('utf-8'))
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "email",
            "name",
            "username",
            "password",
            "favorite_movie",
            "favorite_editor",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

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
            "confirm_email": "required",
        },
        REGISTRATION_FIELD_ORDER=[
            "name",
            "username",
            "email",
            "confirm_email",
            "password",
            "first_name",
            "last_name",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "company",
            "title",
            "job_title",
            "mailing_address",
            "goals",
            "honor_code",
            "terms_of_service",
            "specialty",
            "profession",
        ],
    )
    def test_field_order_override(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content.decode('utf-8'))
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "name",
            "username",
            "email",
            "password",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

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
            "confirm_email": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
        REGISTRATION_FIELD_ORDER=[
            "name",
            "confirm_email",
            "password",
            "first_name",
            "last_name",
            "gender",
            "year_of_birth",
            "level_of_education",
            "company",
            "title",
            "mailing_address",
            "goals",
            "honor_code",
            "terms_of_service",
        ],
    )
    def test_field_order_invalid_override(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content.decode('utf-8'))
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "email",
            "name",
            "username",
            "password",
            "favorite_movie",
            "favorite_editor",

            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

    def test_register(self):
        # Create a new registration
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
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
        response = self.client.get(reverse("dashboard"))
        self.assertHttpOK(response)

    @override_settings(REGISTRATION_EXTRA_FIELDS={
        "level_of_education": "optional",
        "gender": "optional",
        "year_of_birth": "optional",
        "mailing_address": "optional",
        "goals": "optional",
        "country": "required",
    })
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

    @override_settings(REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm')
    @mock.patch('openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm.DUMMY_STORAGE', new_callable=dict)
    @mock.patch(
        'openedx.core.djangoapps.user_api.tests.test_helpers.DummyRegistrationExtensionModel',
    )
    def test_with_extended_form(self, dummy_model, storage_dict):
        dummy_model_instance = mock.Mock()
        dummy_model.return_value = dummy_model_instance
        # Create a new registration
        self.assertEqual(storage_dict, {})
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
            "favorite_movie": "Inception",
            "favorite_editor": "cat",
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

        self.assertEqual(storage_dict, {'favorite_movie': "Inception", "favorite_editor": "cat"})
        self.assertEqual(dummy_model_instance.user, user)

        # Verify that we've been logged in
        # by trying to access a page that requires authentication
        response = self.client.get(reverse("dashboard"))
        self.assertHttpOK(response)

    def test_activation_email(self):
        # Register, which should trigger an activation email
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertHttpOK(response)

        # Verify that the activation email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, [self.EMAIL])
        self.assertEqual(
            sent_email.subject,
            u"Action Required: Activate your {platform} account".format(platform=settings.PLATFORM_NAME)
        )
        self.assertIn(
            u"high-quality {platform} courses".format(platform=settings.PLATFORM_NAME),
            sent_email.body
        )

    @ddt.data(
        {"email": ""},
        {"email": "invalid"},
        {"name": ""},
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
        }

        # Override the valid fields, making the input invalid
        data.update(invalid_fields)

        # Attempt to create the account, expecting an error response
        response = self.client.post(self.url, data)
        self.assertHttpBadRequest(response)

    @override_settings(REGISTRATION_EXTRA_FIELDS={"country": "required"})
    @ddt.data("email", "name", "username", "password", "country")
    def test_register_missing_required_field(self, missing_field):
        data = {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "country": self.COUNTRY,
        }

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
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same email address
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": "someone_else",
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "email": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
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
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": "someone+else@example.com",
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
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
        })
        self.assertHttpOK(response)

        # Try to create a second user with the same username
        response = self.client.post(self.url, {
            "email": self.EMAIL,
            "name": "Someone Else",
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        })
        self.assertEqual(response.status_code, 409)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "username": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
                        "Try again with a different username."
                    ).format(
                        self.USERNAME
                    )
                }],
                "email": [{
                    "user_message": (
                        u"It looks like {} belongs to an existing account. "
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
        })
        self.assertHttpOK(response)

    def test_missing_fields(self):
        response = self.client.post(
            self.url,
            {
                "email": self.EMAIL,
                "name": self.NAME,
                "honor_code": "true",
            }
        )
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                u"username": [{u"user_message": USERNAME_BAD_LENGTH_MSG}],
                u"password": [{u"user_message": u"This field is required."}],
            }
        )

    def test_country_overrides(self):
        """Test that overridden countries are available in country list."""
        # Retrieve the registration form description
        with override_settings(REGISTRATION_EXTRA_FIELDS={"country": "required"}):
            response = self.client.get(self.url)
            self.assertHttpOK(response)

        self.assertContains(response, 'Kosovo')

    def test_password_with_spaces(self):
        """Test that spaces are stripped correctly from password while creating an account."""
        unstripped_password = self.PASSWORD + '  '
        with mock.patch(
            'openedx.core.djangoapps.user_authn.views.register.authenticate_new_user',
            wraps=authenticate_new_user
        ) as mock_authenticate_new_user:
            self.client.post(self.url, {
                "email": self.EMAIL,
                "name": self.NAME,
                "username": self.USERNAME,
                "password": unstripped_password,
                "honor_code": "true",
            })

            mock_authenticate_new_user.assert_called_with(
                mock_authenticate_new_user.call_args[0][0],  # get request object from mock
                self.USERNAME,
                unstripped_password.strip()
            )

    def test_create_account_not_allowed(self):
        """
        Test case to check user creation is forbidden when ALLOW_PUBLIC_ACCOUNT_CREATION feature flag is turned off
        """

        def _side_effect_for_get_value(value, default=None):
            """
            returns a side_effect with given return value for a given value
            """
            if value == 'ALLOW_PUBLIC_ACCOUNT_CREATION':
                return False
            else:
                return get_value(value, default)

        with mock.patch('openedx.core.djangoapps.site_configuration.helpers.get_value') as mock_get_value:
            mock_get_value.side_effect = _side_effect_for_get_value
            response = self.client.post(self.url, {"email": self.EMAIL, "username": self.USERNAME})
            self.assertEqual(response.status_code, 403)

    def _assert_fields_match(self, actual_field, expected_field):
        """
        Assert that the actual field and the expected field values match.
        """
        self.assertIsNot(
            actual_field, None,
            msg=u"Could not find field {name}".format(name=expected_field["name"])
        )

        for key in expected_field:
            self.assertEqual(
                actual_field[key], expected_field[key],
                msg=u"Expected {expected} for {key} but got {actual} instead".format(
                    key=key,
                    actual=actual_field[key],
                    expected=expected_field[key]
                )
            )

    def _populate_always_present_fields(self, field):
        """
        Populate field dictionary with keys and values that are always present.
        """
        defaults = [
            ("label", ""),
            ("instructions", ""),
            ("placeholder", ""),
            ("defaultValue", ""),
            ("restrictions", {}),
            ("errorMessages", {}),
        ]
        field.update({
            key: value
            for key, value in defaults if key not in field
        })

    def _assert_reg_field(self, extra_fields_setting, expected_field):
        """
        Retrieve the registration form description from the server and
        verify that it contains the expected field.

        Args:
            extra_fields_setting (dict): Override the Django setting controlling
                which extra fields are displayed in the form.
            expected_field (dict): The field definition we expect to find in the form.

        Raises:
            AssertionError
        """
        # Add in fields that are always present
        self._populate_always_present_fields(expected_field)

        # Retrieve the registration form description
        with override_settings(REGISTRATION_EXTRA_FIELDS=extra_fields_setting):
            response = self.client.get(self.url)
            self.assertHttpOK(response)

        # Verify that the form description matches what we'd expect
        form_desc = json.loads(response.content.decode('utf-8'))

        actual_field = None
        for field in form_desc["fields"]:
            if field["name"] == expected_field["name"]:
                actual_field = field
                break

        self._assert_fields_match(actual_field, expected_field)

    def _assert_password_field_hidden(self, field_settings):
        self._assert_reg_field(field_settings, {
            "name": "password",
            "type": "hidden",
            "required": False
        })

    def _assert_social_auth_provider_present(self, field_settings, backend):
        self._assert_reg_field(field_settings, {
            "name": "social_auth_provider",
            "type": "hidden",
            "required": False,
            "defaultValue": backend.name
        })


@ddt.ddt
class RegistrationViewTestV2(RegistrationViewTestV1):
    """
    Test for registration api V2

    """
    # pylint: disable=test-inherits-tests

    def setUp(self):  # pylint: disable=arguments-differ
        super(RegistrationViewTestV1, self).setUp()
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
            "confirm_email": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
        REGISTRATION_FIELD_ORDER=[
            "name",
            "confirm_email",
            "password",
            "first_name",
            "last_name",
            "gender",
            "year_of_birth",
            "level_of_education",
            "company",
            "title",
            "mailing_address",
            "goals",
            "honor_code",
            "terms_of_service",
        ],
    )
    def test_field_order_invalid_override(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content.decode('utf-8'))
        field_names = [field["name"] for field in form_desc["fields"]]

        self.assertEqual(field_names, [
            "email",
            "name",
            "username",
            "password",
            "favorite_movie",
            "favorite_editor",
            "confirm_email",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

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
            "confirm_email": "required",
        },
        REGISTRATION_FIELD_ORDER=[
            "name",
            "username",
            "email",
            "confirm_email",
            "password",
            "first_name",
            "last_name",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "company",
            "title",
            "job_title",
            "mailing_address",
            "goals",
            "honor_code",
            "terms_of_service",
            "specialty",
            "profession",
        ],
    )
    def test_field_order_override(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content.decode('utf-8'))
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "name",
            "username",
            "email",
            "confirm_email",
            "password",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

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
            "confirm_email": "required",
        },
        REGISTRATION_EXTENSION_FORM='openedx.core.djangoapps.user_api.tests.test_helpers.TestCaseForm',
    )
    def test_field_order(self):
        response = self.client.get(self.url)
        self.assertHttpOK(response)

        # Verify that all fields render in the correct order
        form_desc = json.loads(response.content.decode('utf-8'))
        field_names = [field["name"] for field in form_desc["fields"]]
        self.assertEqual(field_names, [
            "email",
            "name",
            "username",
            "password",
            "favorite_movie",
            "favorite_editor",
            "confirm_email",
            "city",
            "state",
            "country",
            "gender",
            "year_of_birth",
            "level_of_education",
            "mailing_address",
            "goals",
            "honor_code",
        ])

    def test_registration_form_confirm_email(self):
        self._assert_reg_field(
            {"confirm_email": "required"},
            {
                "name": "confirm_email",
                "type": "email",
                "required": True,
                "label": "Confirm Email",
                "errorMessages": {
                    "required": "The email addresses do not match.",
                }
            }
        )

    def _assert_redirect_url(self, response, expected_redirect_url):
        """
        Assert that the redirect URL is in the response and has the expected value.

        Assumes that response content is well-formed JSON
        (you can call `_assert_response` first to assert this).
        """
        response_dict = json.loads(response.content.decode('utf-8'))
        assert 'redirect_url' in response_dict, (
            "Response JSON unexpectedly does not have redirect_url: {!r}".format(
                response_dict
            )
        )
        assert response_dict['redirect_url'] == expected_redirect_url

    @ddt.data(
        # Default redirect is dashboard.
        {
            'next_url': None,
            'course_id': None,
            'expected_redirect': settings.LMS_ROOT_URL + '/dashboard',
        },
        # Added root url in next .
        {
            'next_url': '/harmless-relative-page',
            'course_id': None,
            'expected_redirect': settings.LMS_ROOT_URL + '/harmless-relative-page',
        },
        # An absolute URL to a non-whitelisted domain is not an acceptable redirect.
        {
            'next_url': 'https://evil.sketchysite',
            'course_id': None,
            'expected_redirect': settings.LMS_ROOT_URL + '/dashboard',
        },
        # An absolute URL to a whitelisted domain is acceptable.
        {
            'next_url': 'https://openedx.service/coolpage',
            'course_id': None,
            'expected_redirect': 'https://openedx.service/coolpage',
        },
        # If course_id is provided, redirect to finish_auth with dashboard as next.
        {
            'next_url': None,
            'course_id': 'coursekey',
            'expected_redirect': (
                '{root_url}/account/finish_auth?course_id=coursekey&next=%2Fdashboard'.
                format(root_url=settings.LMS_ROOT_URL)
            ),
        },
        # If valid course_id AND next_url are provided, redirect to finish_auth with
        # provided next URL.
        {
            'next_url': 'freshpage',
            'course_id': 'coursekey',
            'expected_redirect': (
                settings.LMS_ROOT_URL + '/account/finish_auth?course_id=coursekey&next=freshpage'
            )
        },
        # If course_id is provided with invalid next_url, redirect to finish_auth with
        # course_id and dashboard as next URL.
        {
            'next_url': 'http://scam.scam',
            'course_id': 'coursekey',
            'expected_redirect': (
                '{root_url}/account/finish_auth?course_id=coursekey&next=%2Fdashboard'.
                format(root_url=settings.LMS_ROOT_URL)
            ),
        },
    )
    @ddt.unpack
    @override_settings(LOGIN_REDIRECT_WHITELIST=['openedx.service'])
    @skip_unless_lms
    def test_register_success_with_redirect(self, next_url, course_id, expected_redirect):
        post_params = {
            "email": self.EMAIL,
            "name": self.NAME,
            "username": self.USERNAME,
            "password": self.PASSWORD,
            "honor_code": "true",
        }

        if next_url:
            post_params['next'] = next_url
        if course_id:
            post_params['course_id'] = course_id

        response = self.client.post(
            self.url,
            post_params,
            HTTP_ACCEPT='*/*',
        )
        self._assert_redirect_url(response, expected_redirect)


@httpretty.activate
@ddt.ddt
class ThirdPartyRegistrationTestMixin(ThirdPartyOAuthTestMixin, CacheIsolationTestCase):
    """
    Tests for the User API registration endpoint with 3rd party authentication.
    """
    CREATE_USER = False

    ENABLED_CACHES = ['default']

    __test__ = False

    def setUp(self):
        super(ThirdPartyRegistrationTestMixin, self).setUp()
        self.url = reverse('user_api_registration')

    def tearDown(self):
        super(ThirdPartyRegistrationTestMixin, self).tearDown()
        Partial.objects.all().delete()

    def data(self, user=None):
        """Returns the request data for the endpoint."""
        return {
            "provider": self.BACKEND,
            "access_token": self.access_token,
            "client_id": self.client_id,
            "honor_code": "true",
            "country": "US",
            "username": user.username if user else "test_username",
            "name": user.first_name if user else "test name",
            "email": user.email if user else "test@test.com"
        }

    def _assert_existing_user_error(self, response):
        """Assert that the given response was an error with the given status_code and error code."""
        self.assertEqual(response.status_code, 409)
        errors = json.loads(response.content.decode('utf-8'))
        for conflict_attribute in ["username", "email"]:
            self.assertIn(conflict_attribute, errors)
            self.assertIn("belongs to an existing account", errors[conflict_attribute][0]["user_message"])

    def _assert_access_token_error(self, response, expected_error_message):
        """Assert that the given response was an error for the access_token field with the given error message."""
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "access_token": [{"user_message": expected_error_message}],
            }
        )

    def _assert_third_party_session_expired_error(self, response, expected_error_message):
        """Assert that given response is an error due to third party session expiry"""
        self.assertEqual(response.status_code, 400)
        response_json = json.loads(response.content.decode('utf-8'))
        self.assertDictEqual(
            response_json,
            {
                "session_expired": [{"user_message": expected_error_message}],
            }
        )

    def _verify_user_existence(self, user_exists, social_link_exists, user_is_active=None, username=None):
        """Verifies whether the user object exists."""
        users = User.objects.filter(username=(username if username else "test_username"))
        self.assertEqual(users.exists(), user_exists)
        if user_exists:
            self.assertEqual(users[0].is_active, user_is_active)
            self.assertEqual(
                UserSocialAuth.objects.filter(user=users[0], provider=self.BACKEND).exists(),
                social_link_exists
            )
        else:
            self.assertEqual(UserSocialAuth.objects.count(), 0)

    def test_success(self):
        self._verify_user_existence(user_exists=False, social_link_exists=False)

        self._setup_provider_response(success=True)
        response = self.client.post(self.url, self.data())
        self.assertEqual(response.status_code, 200)

        self._verify_user_existence(user_exists=True, social_link_exists=True, user_is_active=False)

    def test_unlinked_active_user(self):
        user = UserFactory()
        response = self.client.post(self.url, self.data(user))
        self._assert_existing_user_error(response)
        self._verify_user_existence(
            user_exists=True, social_link_exists=False, user_is_active=True, username=user.username
        )

    def test_unlinked_inactive_user(self):
        user = UserFactory(is_active=False)
        response = self.client.post(self.url, self.data(user))
        self._assert_existing_user_error(response)
        self._verify_user_existence(
            user_exists=True, social_link_exists=False, user_is_active=False, username=user.username
        )

    def test_user_already_registered(self):
        self._setup_provider_response(success=True)
        user = UserFactory()
        UserSocialAuth.objects.create(user=user, provider=self.BACKEND, uid=self.social_uid)
        response = self.client.post(self.url, self.data(user))
        self._assert_existing_user_error(response)
        self._verify_user_existence(
            user_exists=True, social_link_exists=True, user_is_active=True, username=user.username
        )

    def test_social_user_conflict(self):
        self._setup_provider_response(success=True)
        user = UserFactory()
        UserSocialAuth.objects.create(user=user, provider=self.BACKEND, uid=self.social_uid)
        response = self.client.post(self.url, self.data())
        self._assert_access_token_error(response, "The provided access_token is already associated with another user.")
        self._verify_user_existence(
            user_exists=True, social_link_exists=True, user_is_active=True, username=user.username
        )

    def test_invalid_token(self):
        self._setup_provider_response(success=False)
        response = self.client.post(self.url, self.data())
        self._assert_access_token_error(response, "The provided access_token is not valid.")
        self._verify_user_existence(user_exists=False, social_link_exists=False)

    def test_missing_token(self):
        data = self.data()
        data.pop("access_token")
        response = self.client.post(self.url, data)
        self._assert_access_token_error(
            response,
            u"An access_token is required when passing value ({}) for provider.".format(self.BACKEND)
        )
        self._verify_user_existence(user_exists=False, social_link_exists=False)

    def test_expired_pipeline(self):
        """
        Test that there is an error and account is not created
        when request is made for account creation using third (Google, Facebook etc) party with pipeline
        getting expired using browser (not mobile application).

        NOTE: We are NOT using actual pipeline here so pipeline is always expired in this environment.
        we don't have to explicitly expire pipeline.
        """
        data = self.data()
        # provider is sent along request when request is made from mobile application
        data.pop("provider")
        # to identify that request is made using browser
        data.update({"social_auth_provider": "Google"})
        response = self.client.post(self.url, data)
        self._assert_third_party_session_expired_error(
            response,
            u"Registration using {provider} has timed out.".format(provider="Google")
        )
        self._verify_user_existence(user_exists=False, social_link_exists=False)


@skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
class TestFacebookRegistrationView(
    ThirdPartyRegistrationTestMixin, ThirdPartyOAuthTestMixinFacebook, TransactionTestCase
):
    """Tests the User API registration endpoint with Facebook authentication."""
    __test__ = True

    def test_social_auth_exception(self):
        """
        According to the do_auth method in social_core.backends.facebook.py,
        the Facebook API sometimes responds back a JSON with just False as value.
        """
        self._setup_provider_response_with_body(200, json.dumps("false"))
        response = self.client.post(self.url, self.data())
        self._assert_access_token_error(response, "The provided access_token is not valid.")
        self._verify_user_existence(user_exists=False, social_link_exists=False)


@skipUnless(settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH"), "third party auth not enabled")
class TestGoogleRegistrationView(
    ThirdPartyRegistrationTestMixin, ThirdPartyOAuthTestMixinGoogle, TransactionTestCase
):
    """Tests the User API registration endpoint with Google authentication."""
    __test__ = True


@ddt.ddt
class RegistrationValidationViewTests(test_utils.ApiTestCase):
    """
    Tests for validity of user data in registration forms.
    """

    endpoint_name = 'registration_validation'
    path = reverse(endpoint_name)

    def setUp(self):
        super(RegistrationValidationViewTests, self).setUp()
        cache.clear()

    def get_validation_decision(self, data):
        response = self.client.post(self.path, data)
        return response.data.get('validation_decisions', {})

    def assertValidationDecision(self, data, decision):
        self.assertEqual(
            self.get_validation_decision(data),
            decision
        )

    def assertNotValidationDecision(self, data, decision):
        self.assertNotEqual(
            self.get_validation_decision(data),
            decision
        )

    def test_no_decision_for_empty_request(self):
        self.assertValidationDecision(
            {},
            {}
        )

    def test_no_decision_for_invalid_request(self):
        self.assertValidationDecision(
            {'invalid_field': 'random_user_data'},
            {}
        )

    @ddt.data(
        ['name', [name for name in testutils.VALID_NAMES]],
        ['email', [email for email in testutils.VALID_EMAILS]],
        ['password', [password for password in testutils.VALID_PASSWORDS]],
        ['username', [username for username in testutils.VALID_USERNAMES]],
        ['country', [country for country in testutils.VALID_COUNTRIES]]
    )
    @ddt.unpack
    def test_positive_validation_decision(self, form_field_name, user_data):
        """
        Test if {0} as any item in {1} gives a positive validation decision.
        """
        self.assertValidationDecision(
            {form_field_name: user_data},
            {form_field_name: ''}
        )

    @ddt.data(
        # Skip None type for invalidity checks.
        ['name', [name for name in testutils.INVALID_NAMES[1:]]],
        ['email', [email for email in testutils.INVALID_EMAILS[1:]]],
        ['password', [password for password in testutils.INVALID_PASSWORDS[1:]]],
        ['username', [username for username in testutils.INVALID_USERNAMES[1:]]],
        ['country', [country for country in testutils.INVALID_COUNTRIES[1:]]]
    )
    @ddt.unpack
    def test_negative_validation_decision(self, form_field_name, user_data):
        """
        Test if {0} as any item in {1} gives a negative validation decision.
        """
        self.assertNotValidationDecision(
            {form_field_name: user_data},
            {form_field_name: ''}
        )

    @ddt.data(
        ['username', 'username@email.com'],  # No conflict
        ['user', 'username@email.com'],  # Username conflict
        ['username', 'user@email.com'],  # Email conflict
        ['user', 'user@email.com']  # Both conflict
    )
    @ddt.unpack
    def test_existence_conflict(self, username, email):
        """
        Test if username '{0}' and email '{1}' have conflicts with
        username 'user' and email 'user@email.com'.
        """
        user = User.objects.create_user(username='user', email='user@email.com')
        self.assertValidationDecision(
            {
                'username': username,
                'email': email
            },
            {
                # pylint: disable=no-member
                "username": USERNAME_CONFLICT_MSG.format(
                    username=user.username
                ) if username == user.username else '',
                # pylint: disable=no-member
                "email": EMAIL_CONFLICT_MSG.format(
                    email_address=user.email
                ) if email == user.email else ''
            }
        )

    @ddt.data('', ('e' * EMAIL_MAX_LENGTH) + '@email.com')
    def test_email_bad_length_validation_decision(self, email):
        self.assertValidationDecision(
            {'email': email},
            {'email': EMAIL_BAD_LENGTH_MSG}
        )

    def test_email_generically_invalid_validation_decision(self):
        email = 'email'
        self.assertValidationDecision(
            {'email': email},
            # pylint: disable=no-member
            {'email': EMAIL_INVALID_MSG.format(email=email)}
        )

    def test_confirm_email_matches_email(self):
        email = 'user@email.com'
        self.assertValidationDecision(
            {'email': email, 'confirm_email': email},
            {'email': '', 'confirm_email': ''}
        )

    @ddt.data('', 'users@other.email')
    def test_confirm_email_doesnt_equal_email(self, confirm_email):
        self.assertValidationDecision(
            {'email': 'user@email.com', 'confirm_email': confirm_email},
            {'email': '', 'confirm_email': six.text_type(REQUIRED_FIELD_CONFIRM_EMAIL_MSG)}
        )

    @ddt.data(
        'u' * (USERNAME_MIN_LENGTH - 1),
        'u' * (USERNAME_MAX_LENGTH + 1)
    )
    def test_username_bad_length_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {'username': six.text_type(USERNAME_BAD_LENGTH_MSG)}
        )

    @skipUnless(settings.FEATURES.get("ENABLE_UNICODE_USERNAME"), "Unicode usernames disabled.")
    @ddt.data(*testutils.INVALID_USERNAMES_UNICODE)
    def test_username_invalid_unicode_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {'username': six.text_type(USERNAME_INVALID_CHARS_UNICODE)}
        )

    @skipIf(settings.FEATURES.get("ENABLE_UNICODE_USERNAME"), "Unicode usernames enabled.")
    @ddt.data(*testutils.INVALID_USERNAMES_ASCII)
    def test_username_invalid_ascii_validation_decision(self, username):
        self.assertValidationDecision(
            {'username': username},
            {"username": six.text_type(USERNAME_INVALID_CHARS_ASCII)}
        )

    def test_password_empty_validation_decision(self):
        # 2 is the default setting for minimum length found in lms/envs/common.py
        # under AUTH_PASSWORD_VALIDATORS.MinimumLengthValidator
        msg = u'This password is too short. It must contain at least 2 characters.'
        self.assertValidationDecision(
            {'password': ''},
            {"password": msg}
        )

    def test_password_bad_min_length_validation_decision(self):
        password = 'p'
        # 2 is the default setting for minimum length found in lms/envs/common.py
        # under AUTH_PASSWORD_VALIDATORS.MinimumLengthValidator
        msg = u'This password is too short. It must contain at least 2 characters.'
        self.assertValidationDecision(
            {'password': password},
            {"password": msg}
        )

    def test_password_bad_max_length_validation_decision(self):
        password = 'p' * DEFAULT_MAX_PASSWORD_LENGTH
        # 75 is the default setting for maximum length found in lms/envs/common.py
        # under AUTH_PASSWORD_VALIDATORS.MaximumLengthValidator
        msg = u'This password is too long. It must contain no more than 75 characters.'
        self.assertValidationDecision(
            {'password': password},
            {"password": msg}
        )

    def test_password_equals_username_validation_decision(self):
        self.assertValidationDecision(
            {"username": "somephrase", "password": "somephrase"},
            {"username": "", "password": u"The password is too similar to the username."}
        )

    @override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'registration_proxy',
            }
        }
    )
    def test_rate_limiting_registration_view(self):
        """
        Confirm rate limits work as expected for registration
        end point /api/user/v1/validation/registration/. Note
        that drf's rate limiting makes use of the default cache
        to enforce limits; that's why this test needs a "real"
        default cache (as opposed to the usual-for-tests DummyCache)
        """
        for _ in range(int(settings.REGISTRATION_VALIDATION_RATELIMIT.split('/')[0])):
            response = self.request_without_auth('post', self.path)
            self.assertNotEqual(response.status_code, 403)
        response = self.request_without_auth('post', self.path)
        self.assertEqual(response.status_code, 403)
