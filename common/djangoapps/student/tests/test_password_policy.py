# -*- coding: utf-8 -*-
"""
This test file will verify proper password policy enforcement, which is an option feature
"""
import json
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch

from openedx.core.djangoapps.external_auth.models import ExternalAuthMap
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.user_authn.views.deprecated import create_account
from util.password_policy_validators import create_validator_config


class TestPasswordPolicy(TestCase):
    """
    Go through some password policy tests to make sure things are properly working
    """
    def setUp(self):
        super(TestPasswordPolicy, self).setUp()
        self.url = reverse('create_account')
        self.request_factory = RequestFactory()
        self.url_params = {
            'username': 'username',
            'email': 'foo_bar@bar.com',
            'name': 'username',
            'terms_of_service': 'true',
            'honor_code': 'true',
        }

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 6})
    ])
    def test_password_length_too_short(self):
        self.url_params['password'] = 'aaa'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password is too short. It must contain at least 6 characters.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 6})
    ])
    def test_password_length_long_enough(self):
        self.url_params['password'] = 'ThisIsALongerPassword'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MaximumLengthValidator', {'max_length': 12})
    ])
    def test_password_length_too_long(self):
        self.url_params['password'] = 'ThisPasswordIsWayTooLong'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password is too long. It must contain no more than 12 characters.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.UppercaseValidator', {'min_upper': 3})
    ])
    def test_password_not_enough_uppercase(self):
        self.url_params['password'] = 'thisshouldfail'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password must contain at least 3 uppercase letters.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.UppercaseValidator', {'min_upper': 3})
    ])
    def test_password_enough_uppercase(self):
        self.url_params['password'] = 'ThisShouldPass'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.LowercaseValidator', {'min_lower': 3})
    ])
    def test_password_not_enough_lowercase(self):
        self.url_params['password'] = 'THISSHOULDFAIL'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password must contain at least 3 lowercase letters.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.LowercaseValidator', {'min_lower': 3})
    ])
    def test_password_enough_lowercase(self):
        self.url_params['password'] = 'ThisShouldPass'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.PunctuationValidator', {'min_punctuation': 3})
    ])
    def test_not_enough_punctuations(self):
        self.url_params['password'] = 'thisshouldfail'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password must contain at least 3 punctuation marks.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.PunctuationValidator', {'min_punctuation': 3})
    ])
    def test_enough_punctuations(self):
        self.url_params['password'] = 'Th!sSh.uldPa$*'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.NumericValidator', {'min_numeric': 3})
    ])
    def test_not_enough_numeric_characters(self):
        # The unicode ២ is the number 2 in Khmer and the ٧ is the Arabic-Indic number 7
        self.url_params['password'] = u'thisShouldFail២٧'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password must contain at least 3 numbers.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.NumericValidator', {'min_numeric': 3})
    ])
    def test_enough_numeric_characters(self):
        # The unicode ២ is the number 2 in Khmer
        self.url_params['password'] = u'thisShouldPass២33'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.AlphabeticValidator', {'min_alphabetic': 3})
    ])
    def test_not_enough_alphabetic_characters(self):
        self.url_params['password'] = '123456ab'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password must contain at least 3 letters.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.AlphabeticValidator', {'min_alphabetic': 3})
    ])
    def test_enough_alphabetic_characters(self):
        self.url_params['password'] = u'𝒯𝓗Ï𝓼𝒫å𝓼𝓼𝔼𝓼'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 3}),
        create_validator_config('util.password_policy_validators.UppercaseValidator', {'min_upper': 3}),
        create_validator_config('util.password_policy_validators.NumericValidator', {'min_numeric': 3}),
        create_validator_config('util.password_policy_validators.PunctuationValidator', {'min_punctuation': 3}),
    ])
    def test_multiple_errors_fail(self):
        self.url_params['password'] = 'thisshouldfail'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        errstring = (
            "This password must contain at least 3 uppercase letters. "
            "This password must contain at least 3 numbers. "
            "This password must contain at least 3 punctuation marks."
        )
        self.assertEqual(obj['value'], errstring)

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 3}),
        create_validator_config('util.password_policy_validators.UppercaseValidator', {'min_upper': 3}),
        create_validator_config('util.password_policy_validators.LowercaseValidator', {'min_lower': 3}),
        create_validator_config('util.password_policy_validators.NumericValidator', {'min_numeric': 3}),
        create_validator_config('util.password_policy_validators.PunctuationValidator', {'min_punctuation': 3}),
    ])
    def test_multiple_errors_pass(self):
        self.url_params['password'] = u'tH1s Sh0u!d P3#$!'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('django.contrib.auth.password_validation.CommonPasswordValidator')
    ])
    def test_common_password_fail(self):
        self.url_params['password'] = 'password'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "This password is too common.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('django.contrib.auth.password_validation.CommonPasswordValidator')
    ])
    def test_common_password_pass(self):
        self.url_params['password'] = 'this_is_ok'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 6}),
        create_validator_config('util.password_policy_validators.MaximumLengthValidator', {'max_length': 75}),
    ])
    def test_with_unicode(self):
        self.url_params['password'] = u'四節比分和七年前'
        response = self.client.post(self.url, self.url_params)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('util.password_policy_validators.MinimumLengthValidator', {'min_length': 6})
    ], SESSION_ENGINE='django.contrib.sessions.backends.cache')
    def test_ext_auth_password_length_too_short(self):
        """
        Tests that even if password policy is enforced, ext_auth registrations aren't subject to it
        """
        self.url_params['password'] = u'aaa'  # shouldn't pass validation
        request = self.request_factory.post(self.url, self.url_params)
        request.site = SiteFactory.create()
        # now indicate we are doing ext_auth by setting 'ExternalAuthMap' in the session.
        request.session = import_module(settings.SESSION_ENGINE).SessionStore()  # empty session
        extauth = ExternalAuthMap(external_id='withmap@stanford.edu',
                                  external_email='withmap@stanford.edu',
                                  internal_password=self.url_params['password'],
                                  external_domain='shib:https://idp.stanford.edu/')
        request.session['ExternalAuthMap'] = extauth
        request.user = AnonymousUser()

        with patch('edxmako.request_context.get_current_request', return_value=request):
            response = create_account(request)
        self.assertEqual(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])


class TestUsernamePasswordNonmatch(TestCase):
    """
    Test that registration username and password fields differ
    """
    def setUp(self):
        super(TestUsernamePasswordNonmatch, self).setUp()
        self.url = reverse('create_account')

        self.url_params = {
            'username': 'username',
            'email': 'foo_bar@bar.com',
            'name': 'username',
            'terms_of_service': 'true',
            'honor_code': 'true',
        }

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('django.contrib.auth.password_validation.UserAttributeSimilarityValidator')
    ])
    def test_with_username_password_match(self):
        self.url_params['username'] = "foobar"
        self.url_params['password'] = "foobar"
        response = self.client.post(self.url, self.url_params)
        self.assertEquals(response.status_code, 400)
        obj = json.loads(response.content)
        self.assertEqual(
            obj['value'],
            "The password is too similar to the username.",
        )

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config('django.contrib.auth.password_validation.UserAttributeSimilarityValidator')
    ])
    def test_with_username_password_nonmatch(self):
        self.url_params['username'] = "foobar"
        self.url_params['password'] = "nonmatch"
        response = self.client.post(self.url, self.url_params)
        self.assertEquals(response.status_code, 200)
        obj = json.loads(response.content)
        self.assertTrue(obj['success'])
