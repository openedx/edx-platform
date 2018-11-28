# -*- coding: utf-8 -*-
"""Tests for account creation"""
import json
import unittest
from datetime import datetime
from importlib import import_module
import unicodedata

import ddt
import mock
import pytz
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.urls import reverse
from django.test import TestCase, TransactionTestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.contrib.auth.hashers import make_password

from django_comment_common.models import ForumsConfig
from notification_prefs import NOTIFICATION_PREF_KEY
from openedx.core.djangoapps.user_authn.views.deprecated import create_account
from openedx.core.djangoapps.user_authn.views.register import (
    REGISTRATION_AFFILIATE_ID, REGISTRATION_UTM_CREATED_AT, REGISTRATION_UTM_PARAMETERS,
    _skip_activation_email,
)
from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangoapps.user_api.accounts import (
    USERNAME_BAD_LENGTH_MSG, USERNAME_INVALID_CHARS_ASCII, USERNAME_INVALID_CHARS_UNICODE
)
from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, waffle
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from student.models import UserAttribute
from student.tests.factories import UserFactory
from third_party_auth.tests import factories as third_party_auth_factory

TEST_CS_URL = 'https://comments.service.test:123/'

TEST_USERNAME = 'test_user'
TEST_EMAIL = 'test@test.com'


def get_mock_pipeline_data(username=TEST_USERNAME, email=TEST_EMAIL):
    """
    Return mock pipeline data.
    """
    return {
        'backend': 'tpa-saml',
        'kwargs': {
            'username': username,
            'auth_entry': 'register',
            'request': {
                'SAMLResponse': [],
                'RelayState': [
                    'testshib-openedx'
                ]
            },
            'is_new': True,
            'new_association': True,
            'user': None,
            'social': None,
            'details': {
                'username': username,
                'fullname': 'Test Test',
                'last_name': 'Test',
                'first_name': 'Test',
                'email': email,
            },
            'response': {},
            'uid': 'testshib-openedx:{}'.format(username)
        }
    }


@ddt.ddt
@override_settings(
    MICROSITE_CONFIGURATION={
        "microsite": {
            "domain_prefix": "microsite",
            "extended_profile_fields": ["extra1", "extra2"],
        }
    },
    REGISTRATION_EXTRA_FIELDS={
        key: "optional"
        for key in [
            "level_of_education", "gender", "mailing_address", "city", "country", "goals",
            "year_of_birth"
        ]
    }
)
class TestCreateAccount(SiteMixin, TestCase):
    """Tests for account creation"""

    def setUp(self):
        super(TestCreateAccount, self).setUp()
        self.username = "test_user"
        self.url = reverse("create_account")
        self.request_factory = RequestFactory()
        self.params = {
            "username": self.username,
            "email": "test@example.org",
            "password": u"testpass",
            "name": "Test User",
            "honor_code": "true",
            "terms_of_service": "true",
        }

    @ddt.data("en", "eo")
    def test_default_lang_pref_saved(self, lang):
        with mock.patch("django.conf.settings.LANGUAGE_CODE", lang):
            response = self.client.post(self.url, self.params)
            self.assertEqual(response.status_code, 200)
            user = User.objects.get(username=self.username)
            self.assertEqual(get_user_preference(user, LANGUAGE_KEY), lang)

    @ddt.data("en", "eo")
    def test_header_lang_pref_saved(self, lang):
        response = self.client.post(self.url, self.params, HTTP_ACCEPT_LANGUAGE=lang)
        user = User.objects.get(username=self.username)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_preference(user, LANGUAGE_KEY), lang)

    def create_account_and_fetch_profile(self, host='microsite.example.com'):
        """
        Create an account with self.params, assert that the response indicates
        success, and return the UserProfile object for the newly created user
        """
        response = self.client.post(self.url, self.params, HTTP_HOST=host)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username=self.username)
        return user.profile

    def test_create_account_and_normalize_password(self):
        """
        Test that unicode normalization on passwords is happening when a user registers.
        """
        # Set user password to NFKD format so that we can test that it is normalized to
        # NFKC format upon account creation.
        self.params['password'] = unicodedata.normalize('NFKD', u'Ṗŕệṿïệẅ Ṯệẍt')
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)

        user = User.objects.get(username=self.username)
        salt_val = user.password.split('$')[1]

        expected_user_password = make_password(unicodedata.normalize('NFKC', u'Ṗŕệṿïệẅ Ṯệẍt'), salt_val)
        self.assertEqual(expected_user_password, user.password)

    def test_marketing_cookie(self):
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.EDXMKTG_LOGGED_IN_COOKIE_NAME, self.client.cookies)
        self.assertIn(settings.EDXMKTG_USER_INFO_COOKIE_NAME, self.client.cookies)

    @unittest.skipUnless(
        "microsite_configuration.middleware.MicrositeMiddleware" in settings.MIDDLEWARE_CLASSES,
        "Microsites not implemented in this environment"
    )
    def test_profile_saved_no_optional_fields(self):
        profile = self.create_account_and_fetch_profile()
        self.assertEqual(profile.name, self.params["name"])
        self.assertEqual(profile.level_of_education, "")
        self.assertEqual(profile.gender, "")
        self.assertEqual(profile.mailing_address, "")
        self.assertEqual(profile.city, "")
        self.assertEqual(profile.country, "")
        self.assertEqual(profile.goals, "")
        self.assertEqual(
            profile.get_meta(),
            {
                "extra1": "",
                "extra2": "",
            }
        )
        self.assertIsNone(profile.year_of_birth)

    @unittest.skipUnless(
        "microsite_configuration.middleware.MicrositeMiddleware" in settings.MIDDLEWARE_CLASSES,
        "Microsites not implemented in this environment"
    )
    @override_settings(LMS_SEGMENT_KEY="testkey")
    @mock.patch('openedx.core.djangoapps.user_authn.views.register.segment.track')
    @mock.patch('openedx.core.djangoapps.user_authn.views.register.segment.identify')
    def test_segment_tracking(self, mock_segment_identify, _):
        year = datetime.now().year
        year_of_birth = year - 14
        self.params.update({
            "level_of_education": "a",
            "gender": "o",
            "mailing_address": "123 Example Rd",
            "city": "Exampleton",
            "country": "US",
            "goals": "To test this feature",
            "year_of_birth": str(year_of_birth),
            "extra1": "extra_value1",
            "extra2": "extra_value2",
        })

        expected_payload = {
            'email': self.params['email'],
            'username': self.params['username'],
            'name': self.params['name'],
            'age': 13,
            'yearOfBirth': year_of_birth,
            'education': 'Associate degree',
            'address': self.params['mailing_address'],
            'gender': 'Other/Prefer Not to Say',
            'country': self.params['country'],
        }

        profile = self.create_account_and_fetch_profile()

        mock_segment_identify.assert_called_with(profile.user.id, expected_payload)

    @unittest.skipUnless(
        "microsite_configuration.middleware.MicrositeMiddleware" in settings.MIDDLEWARE_CLASSES,
        "Microsites not implemented in this environment"
    )
    def test_profile_saved_all_optional_fields(self):
        self.params.update({
            "level_of_education": "a",
            "gender": "o",
            "mailing_address": "123 Example Rd",
            "city": "Exampleton",
            "country": "US",
            "goals": "To test this feature",
            "year_of_birth": "2015",
            "extra1": "extra_value1",
            "extra2": "extra_value2",
        })
        profile = self.create_account_and_fetch_profile()
        self.assertEqual(profile.level_of_education, "a")
        self.assertEqual(profile.gender, "o")
        self.assertEqual(profile.mailing_address, "123 Example Rd")
        self.assertEqual(profile.city, "Exampleton")
        self.assertEqual(profile.country, "US")
        self.assertEqual(profile.goals, "To test this feature")
        self.assertEqual(
            profile.get_meta(),
            {
                "extra1": "extra_value1",
                "extra2": "extra_value2",
            }
        )
        self.assertEqual(profile.year_of_birth, 2015)

    @unittest.skipUnless(
        "microsite_configuration.middleware.MicrositeMiddleware" in settings.MIDDLEWARE_CLASSES,
        "Microsites not implemented in this environment"
    )
    def test_profile_saved_empty_optional_fields(self):
        self.params.update({
            "level_of_education": "",
            "gender": "",
            "mailing_address": "",
            "city": "",
            "country": "",
            "goals": "",
            "year_of_birth": "",
            "extra1": "",
            "extra2": "",
        })
        profile = self.create_account_and_fetch_profile()
        self.assertEqual(profile.level_of_education, "")
        self.assertEqual(profile.gender, "")
        self.assertEqual(profile.mailing_address, "")
        self.assertEqual(profile.city, "")
        self.assertEqual(profile.country, "")
        self.assertEqual(profile.goals, "")
        self.assertEqual(
            profile.get_meta(),
            {"extra1": "", "extra2": ""}
        )
        self.assertEqual(profile.year_of_birth, None)

    def test_profile_year_of_birth_non_integer(self):
        self.params["year_of_birth"] = "not_an_integer"
        profile = self.create_account_and_fetch_profile()
        self.assertIsNone(profile.year_of_birth)

    def base_extauth_bypass_sending_activation_email(self, bypass_activation_email):
        """
        Tests user creation without sending activation email when
        doing external auth
        """

        request = self.request_factory.post(self.url, self.params)
        request.site = self.site
        # now indicate we are doing ext_auth by setting 'ExternalAuthMap' in the session.
        request.session = import_module(settings.SESSION_ENGINE).SessionStore()  # empty session
        extauth = ExternalAuthMap(external_id='withmap@stanford.edu',
                                  external_email='withmap@stanford.edu',
                                  internal_password=self.params['password'],
                                  external_domain='shib:https://idp.stanford.edu/')
        request.session['ExternalAuthMap'] = extauth
        request.user = AnonymousUser()

        with mock.patch('edxmako.request_context.get_current_request', return_value=request):
            with mock.patch('django.core.mail.send_mail') as mock_send_mail:
                create_account(request)

        # check that send_mail is called
        if bypass_activation_email:
            self.assertFalse(mock_send_mail.called)
        else:
            self.assertTrue(mock_send_mail.called)

    @unittest.skipUnless(settings.FEATURES.get('AUTH_USE_SHIB'), "AUTH_USE_SHIB not set")
    @mock.patch.dict(settings.FEATURES,
                     {'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': True, 'AUTOMATIC_AUTH_FOR_TESTING': False})
    def test_extauth_bypass_sending_activation_email_with_bypass(self):
        """
        Tests user creation without sending activation email when
        settings.FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH']=True and doing external auth
        """
        self.base_extauth_bypass_sending_activation_email(True)

    @unittest.skipUnless(settings.FEATURES.get('AUTH_USE_SHIB'), "AUTH_USE_SHIB not set")
    @mock.patch.dict(settings.FEATURES,
                     {'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False, 'AUTOMATIC_AUTH_FOR_TESTING': False})
    def test_extauth_bypass_sending_activation_email_without_bypass_1(self):
        """
        Tests user creation without sending activation email when
        settings.FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH']=False and doing external auth
        """
        self.base_extauth_bypass_sending_activation_email(False)

    @unittest.skipUnless(settings.FEATURES.get('AUTH_USE_SHIB'), "AUTH_USE_SHIB not set")
    @mock.patch.dict(settings.FEATURES, {'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False,
                                         'AUTOMATIC_AUTH_FOR_TESTING': False, 'SKIP_EMAIL_VALIDATION': True})
    def test_extauth_bypass_sending_activation_email_without_bypass_2(self):
        """
        Tests user creation without sending activation email when
        settings.FEATURES['BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH']=False and doing external auth
        """
        self.base_extauth_bypass_sending_activation_email(True)

    @ddt.data(True, False)
    def test_discussions_email_digest_pref(self, digest_enabled):
        with mock.patch.dict("student.models.settings.FEATURES", {"ENABLE_DISCUSSION_EMAIL_DIGEST": digest_enabled}):
            response = self.client.post(self.url, self.params)
            self.assertEqual(response.status_code, 200)
            user = User.objects.get(username=self.username)
            preference = get_user_preference(user, NOTIFICATION_PREF_KEY)
            if digest_enabled:
                self.assertIsNotNone(preference)
            else:
                self.assertIsNone(preference)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_affiliate_referral_attribution(self):
        """
        Verify that a referral attribution is recorded if an affiliate
        cookie is present upon a new user's registration.
        """
        affiliate_id = 'test-partner'
        self.client.cookies[settings.AFFILIATE_COOKIE_NAME] = affiliate_id
        user = self.create_account_and_fetch_profile().user
        self.assertEqual(UserAttribute.get_user_attribute(user, REGISTRATION_AFFILIATE_ID), affiliate_id)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_utm_referral_attribution(self):
        """
        Verify that a referral attribution is recorded if an affiliate
        cookie is present upon a new user's registration.
        """
        utm_cookie_name = 'edx.test.utm'
        with mock.patch('student.models.RegistrationCookieConfiguration.current') as config:
            instance = config.return_value
            instance.utm_cookie_name = utm_cookie_name

            timestamp = 1475521816879
            utm_cookie = {
                'utm_source': 'test-source',
                'utm_medium': 'test-medium',
                'utm_campaign': 'test-campaign',
                'utm_term': 'test-term',
                'utm_content': 'test-content',
                'created_at': timestamp
            }

            created_at = datetime.fromtimestamp(timestamp / float(1000), tz=pytz.UTC)

            self.client.cookies[utm_cookie_name] = json.dumps(utm_cookie)
            user = self.create_account_and_fetch_profile().user
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_source')),
                utm_cookie.get('utm_source')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_medium')),
                utm_cookie.get('utm_medium')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_campaign')),
                utm_cookie.get('utm_campaign')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_term')),
                utm_cookie.get('utm_term')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_content')),
                utm_cookie.get('utm_content')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_CREATED_AT),
                str(created_at)
            )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_no_referral(self):
        """Verify that no referral is recorded when a cookie is not present."""
        utm_cookie_name = 'edx.test.utm'
        with mock.patch('student.models.RegistrationCookieConfiguration.current') as config:
            instance = config.return_value
            instance.utm_cookie_name = utm_cookie_name

            self.assertIsNone(self.client.cookies.get(settings.AFFILIATE_COOKIE_NAME))
            self.assertIsNone(self.client.cookies.get(utm_cookie_name))
            user = self.create_account_and_fetch_profile().user
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_AFFILIATE_ID))
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_source')))
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_medium')))
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_campaign')))
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_term')))
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_content')))
            self.assertIsNone(UserAttribute.get_user_attribute(user, REGISTRATION_UTM_CREATED_AT))

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_incomplete_utm_referral(self):
        """Verify that no referral is recorded when a cookie is not present."""
        utm_cookie_name = 'edx.test.utm'
        with mock.patch('student.models.RegistrationCookieConfiguration.current') as config:
            instance = config.return_value
            instance.utm_cookie_name = utm_cookie_name

            utm_cookie = {
                'utm_source': 'test-source',
                'utm_medium': 'test-medium',
                # No campaign
                'utm_term': 'test-term',
                'utm_content': 'test-content',
                # No created at
            }

            self.client.cookies[utm_cookie_name] = json.dumps(utm_cookie)
            user = self.create_account_and_fetch_profile().user

            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_source')),
                utm_cookie.get('utm_source')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_medium')),
                utm_cookie.get('utm_medium')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_term')),
                utm_cookie.get('utm_term')
            )
            self.assertEqual(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_content')),
                utm_cookie.get('utm_content')
            )
            self.assertIsNone(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_PARAMETERS.get('utm_campaign'))
            )
            self.assertIsNone(
                UserAttribute.get_user_attribute(user, REGISTRATION_UTM_CREATED_AT)
            )

    @mock.patch("openedx.core.djangoapps.site_configuration.helpers.get_value", mock.Mock(return_value=False))
    def test_create_account_not_allowed(self):
        """
        Test case to check user creation is forbidden when ALLOW_PUBLIC_ACCOUNT_CREATION feature flag is turned off
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_create_account_prevent_auth_user_writes(self):
        with waffle().override(PREVENT_AUTH_USER_WRITES, True):
            response = self.client.get(self.url)
            assert response.status_code == 403

    def test_created_on_site_user_attribute_set(self):
        profile = self.create_account_and_fetch_profile(host=self.site.domain)
        self.assertEqual(UserAttribute.get_user_attribute(profile.user, 'created_on_site'), self.site.domain)

    @ddt.data(
        (
            False, False, get_mock_pipeline_data(),
            {
                'SKIP_EMAIL_VALIDATION': False, 'AUTOMATIC_AUTH_FOR_TESTING': False,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False,
            },
            False  # Do not skip activation email for normal scenario.
        ),
        (
            False, False, get_mock_pipeline_data(),
            {
                'SKIP_EMAIL_VALIDATION': True, 'AUTOMATIC_AUTH_FOR_TESTING': False,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False,
            },
            True  # Skip activation email when `SKIP_EMAIL_VALIDATION` FEATURE flag is active.
        ),
        (
            False, False, get_mock_pipeline_data(),
            {
                'SKIP_EMAIL_VALIDATION': False, 'AUTOMATIC_AUTH_FOR_TESTING': True,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False,
            },
            True  # Skip activation email when `AUTOMATIC_AUTH_FOR_TESTING` FEATURE flag is active.
        ),
        (
            True, False, get_mock_pipeline_data(),
            {
                'SKIP_EMAIL_VALIDATION': False, 'AUTOMATIC_AUTH_FOR_TESTING': False,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': True,
            },
            True  # Skip activation email for external auth scenario.
        ),
        (
            False, False, get_mock_pipeline_data(),
            {
                'SKIP_EMAIL_VALIDATION': False, 'AUTOMATIC_AUTH_FOR_TESTING': False,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': True,
            },
            False  # Do not skip activation email when `BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH` feature flag is set
                   # but it is not external auth scenario.
        ),
        (
            False, True, get_mock_pipeline_data(),
            {
                'SKIP_EMAIL_VALIDATION': False, 'AUTOMATIC_AUTH_FOR_TESTING': False,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False,
            },
            True  # Skip activation email if `skip_email_verification` is set for third party authentication.
        ),
        (
            False, False, get_mock_pipeline_data(email='invalid@yopmail.com'),
            {
                'SKIP_EMAIL_VALIDATION': False, 'AUTOMATIC_AUTH_FOR_TESTING': False,
                'BYPASS_ACTIVATION_EMAIL_FOR_EXTAUTH': False,
            },
            False  # Send activation email when `skip_email_verification` is not set.
        )
    )
    @ddt.unpack
    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_should_skip_activation_email(
            self, do_external_auth, skip_email_verification, running_pipeline, feature_overrides, expected,
    ):
        """
        Test `skip_activation_email` works as expected.
        """
        third_party_provider = third_party_auth_factory.SAMLProviderConfigFactory(
            skip_email_verification=skip_email_verification,
        )
        user = UserFactory(username=TEST_USERNAME, email=TEST_EMAIL)

        with override_settings(FEATURES=dict(settings.FEATURES, **feature_overrides)):
            result = _skip_activation_email(
                user=user,
                do_external_auth=do_external_auth,
                running_pipeline=running_pipeline,
                third_party_provider=third_party_provider
            )

            assert result == expected


@ddt.ddt
class TestCreateAccountValidation(TestCase):
    """
    Test validation of various parameters in the create_account view
    """
    def setUp(self):
        super(TestCreateAccountValidation, self).setUp()
        self.url = reverse("create_account")
        self.minimal_params = {
            "username": "test_username",
            "email": "test_email@example.com",
            "password": "test_password",
            "name": "Test Name",
            "honor_code": "true",
            "terms_of_service": "true",
        }

    def assert_success(self, params):
        """
        Request account creation with the given params and assert that the
        response properly indicates success
        """
        response = self.client.post(self.url, params)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])

    def assert_error(self, params, expected_field, expected_value):
        """
        Request account creation with the given params and assert that the
        response properly indicates an error with the given field and value
        """
        response = self.client.post(self.url, params)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["field"], expected_field)
        self.assertEqual(response_data["value"], expected_value)

    def test_minimal_success(self):
        self.assert_success(self.minimal_params)

    def test_username(self):
        params = dict(self.minimal_params)

        def assert_username_error(expected_error):
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, "username", expected_error)

        # Missing
        del params["username"]
        assert_username_error(USERNAME_BAD_LENGTH_MSG)

        # Empty, too short
        for username in ["", "a"]:
            params["username"] = username
            assert_username_error(USERNAME_BAD_LENGTH_MSG)

        # Too long
        params["username"] = "this_username_has_31_characters"
        assert_username_error(USERNAME_BAD_LENGTH_MSG)

        # Invalid
        params["username"] = "invalid username"
        assert_username_error(str(USERNAME_INVALID_CHARS_ASCII))

    def test_email(self):
        params = dict(self.minimal_params)

        def assert_email_error(expected_error):
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, "email", expected_error)

        # Missing
        del params["email"]
        assert_email_error("A properly formatted e-mail is required")

        # Empty
        params["email"] = ""
        assert_email_error("A properly formatted e-mail is required")

        #too short
        params["email"] = "a"
        assert_email_error("A properly formatted e-mail is required "
                           "Ensure this value has at least 3 characters (it has 1).")

        # Too long
        params["email"] = '{email}@example.com'.format(
            email='this_email_address_has_254_characters_in_it_so_it_is_unacceptable' * 4
        )

        # Assert that we get error when email has more than 254 characters.
        self.assertGreater(len(params['email']), 254)
        assert_email_error("Email cannot be more than 254 characters long")

        # Valid Email
        params["email"] = "student@edx.com"
        # Assert success on valid email
        self.assertLess(len(params["email"]), 254)
        self.assert_success(params)

        # Invalid
        params["email"] = "not_an_email_address"
        assert_email_error("A properly formatted e-mail is required")

    @override_settings(
        REGISTRATION_EMAIL_PATTERNS_ALLOWED=[
            r'.*@edx.org',  # Naive regex omitting '^', '$' and '\.' should still work.
            r'^.*@(.*\.)?example\.com$',
            r'^(^\w+\.\w+)@school.tld$',
        ]
    )
    @ddt.data(
        ('bob@we-are.bad', False),
        ('bob@edx.org.we-are.bad', False),
        ('staff@edx.org', True),
        ('student@example.com', True),
        ('student@sub.example.com', True),
        ('mr.teacher@school.tld', True),
        ('student1234@school.tld', False),
    )
    @ddt.unpack
    def test_email_pattern_requirements(self, email, expect_success):
        """
        Test the REGISTRATION_EMAIL_PATTERNS_ALLOWED setting, a feature which
        can be used to only allow people register if their email matches a
        against a whitelist of regexs.
        """
        params = dict(self.minimal_params)
        params["email"] = email
        if expect_success:
            self.assert_success(params)
        else:
            self.assert_error(params, "email", "Unauthorized email address.")

    def test_password(self):
        params = dict(self.minimal_params)

        def assert_password_error(expected_error):
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, "password", expected_error)

        # Missing
        del params["password"]
        assert_password_error("This field is required.")

        # Empty
        params["password"] = ""
        assert_password_error("This field is required.")

        # Too short
        params["password"] = "a"
        assert_password_error("This password is too short. It must contain at least 2 characters.")

        # Password policy is tested elsewhere

        # Matching username
        params["username"] = params["password"] = "test_username_and_password"
        assert_password_error("The password is too similar to the username.")

    def test_name(self):
        params = dict(self.minimal_params)

        def assert_name_error(expected_error):
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, "name", expected_error)

        # Missing
        del params["name"]
        assert_name_error("Your legal name must be a minimum of two characters long")

        # Empty, too short
        for name in ["", "a"]:
            params["name"] = name
            assert_name_error("Your legal name must be a minimum of two characters long")

    def test_honor_code(self):
        params = dict(self.minimal_params)

        def assert_honor_code_error(expected_error):
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, "honor_code", expected_error)

        with override_settings(REGISTRATION_EXTRA_FIELDS={"honor_code": "required"}):
            # Missing
            del params["honor_code"]
            assert_honor_code_error("To enroll, you must follow the honor code.")

            # Empty, invalid
            for honor_code in ["", "false", "not_boolean"]:
                params["honor_code"] = honor_code
                assert_honor_code_error("To enroll, you must follow the honor code.")

            # True
            params["honor_code"] = "tRUe"
            self.assert_success(params)

        with override_settings(REGISTRATION_EXTRA_FIELDS={"honor_code": "optional"}):
            # Missing
            del params["honor_code"]
            # Need to change username/email because user was created above
            params["username"] = "another_test_username"
            params["email"] = "another_test_email@example.com"
            self.assert_success(params)

    def test_terms_of_service(self):
        params = dict(self.minimal_params)

        def assert_terms_of_service_error(expected_error):
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, "terms_of_service", expected_error)

        # Missing
        del params["terms_of_service"]
        assert_terms_of_service_error("You must accept the terms of service.")

        # Empty, invalid
        for terms_of_service in ["", "false", "not_boolean"]:
            params["terms_of_service"] = terms_of_service
            assert_terms_of_service_error("You must accept the terms of service.")

        # True
        params["terms_of_service"] = "tRUe"
        self.assert_success(params)

    @ddt.data(
        ("level_of_education", 1, "A level of education is required"),
        ("gender", 1, "Your gender is required"),
        ("year_of_birth", 2, "Your year of birth is required"),
        ("mailing_address", 2, "Your mailing address is required"),
        ("goals", 2, "A description of your goals is required"),
        ("city", 2, "A city is required"),
        ("country", 2, "A country is required"),
        ("custom_field", 2, "You are missing one or more required fields")
    )
    @ddt.unpack
    def test_extra_fields(self, field, min_length, expected_error):
        params = dict(self.minimal_params)

        def assert_extra_field_error():
            """
            Assert that requesting account creation results in the expected
            error
            """
            self.assert_error(params, field, expected_error)

        with override_settings(REGISTRATION_EXTRA_FIELDS={field: "required"}):
            # Missing
            assert_extra_field_error()

            # Empty
            params[field] = ""
            assert_extra_field_error()

            # Too short
            if min_length > 1:
                params[field] = "a"
                assert_extra_field_error()


@mock.patch.dict("student.models.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
@mock.patch("lms.lib.comment_client.User.base_url", TEST_CS_URL)
@mock.patch("lms.lib.comment_client.utils.requests.request", return_value=mock.Mock(status_code=200, text='{}'))
class TestCreateCommentsServiceUser(TransactionTestCase):
    """ Tests for creating comments service user. """

    def setUp(self):
        super(TestCreateCommentsServiceUser, self).setUp()
        self.username = "test_user"
        self.url = reverse("create_account")
        self.params = {
            "username": self.username,
            "email": "test@example.org",
            "password": "testpass",
            "name": "Test User",
            "honor_code": "true",
            "terms_of_service": "true",
        }

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    def test_cs_user_created(self, request):
        "If user account creation succeeds, we should create a comments service user"
        response = self.client.post(self.url, self.params)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(request.called)
        args, kwargs = request.call_args
        self.assertEqual(args[0], 'put')
        self.assertTrue(args[1].startswith(TEST_CS_URL))
        self.assertEqual(kwargs['data']['username'], self.params['username'])

    @mock.patch("student.models.Registration.register", side_effect=Exception)
    def test_cs_user_not_created(self, register, request):
        "If user account creation fails, we should not create a comments service user"
        try:
            self.client.post(self.url, self.params)
        except:  # pylint: disable=bare-except
            pass
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username=self.username)
        self.assertTrue(register.called)
        self.assertFalse(request.called)


class TestUnicodeUsername(TestCase):
    """
    Test for Unicode usernames which is an optional feature.
    """

    def setUp(self):
        super(TestUnicodeUsername, self).setUp()
        self.url = reverse('create_account')

        # The word below reads "Omar II", in Arabic. It also contains a space and
        # an Eastern Arabic Number another option is to use the Esperanto fake
        # language but this was used instead to test non-western letters.
        self.username = u'عمر ٢'

        self.url_params = {
            'username': self.username,
            'email': 'unicode_user@example.com',
            "password": "testpass",
            'name': 'unicode_user',
            'terms_of_service': 'true',
            'honor_code': 'true',
        }

    @mock.patch.dict(settings.FEATURES, {'ENABLE_UNICODE_USERNAME': False})
    def test_with_feature_disabled(self):
        """
        Ensures backward-compatible defaults.
        """
        response = self.client.post(self.url, self.url_params)

        self.assertEquals(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEquals(USERNAME_INVALID_CHARS_ASCII, obj['value'])

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email=self.url_params['email'])

    @mock.patch.dict(settings.FEATURES, {'ENABLE_UNICODE_USERNAME': True})
    def test_with_feature_enabled(self):
        response = self.client.post(self.url, self.url_params)
        self.assertEquals(response.status_code, 200)

        self.assertTrue(User.objects.get(email=self.url_params['email']))

    @mock.patch.dict(settings.FEATURES, {'ENABLE_UNICODE_USERNAME': True})
    def test_special_chars_with_feature_enabled(self):
        """
        Ensures that special chars are still prevented.
        """

        invalid_params = self.url_params.copy()
        invalid_params['username'] = '**john**'

        response = self.client.post(self.url, invalid_params)
        self.assertEquals(response.status_code, 400)

        obj = json.loads(response.content)
        self.assertEquals(USERNAME_INVALID_CHARS_UNICODE, obj['value'])

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email=self.url_params['email'])
