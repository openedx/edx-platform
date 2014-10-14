# -*- coding: utf-8 -*-
""" Tests for student profile views. """

from urllib import urlencode
import json

from mock import patch
import ddt
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from util.testing import UrlResetMixin
from user_api.api import account as account_api
from user_api.api import profile as profile_api
from lang_pref import LANGUAGE_KEY, api as language_api


@ddt.ddt
class StudentProfileViewTest(UrlResetMixin, TestCase):
    """ Tests for the student profile views. """

    USERNAME = u'heisenberg'
    PASSWORD = u'ḅḷüëṡḳÿ'
    EMAIL = u'walt@savewalterwhite.com'
    FULL_NAME = u'𝖂𝖆𝖑𝖙𝖊𝖗 𝖂𝖍𝖎𝖙𝖊'

    TEST_LANGUAGE = language_api.Language('eo', u'Dummy language')

    INVALID_LANGUAGE_CODES = [
        '',
        'foo',
        'en@pirate',
    ]

    @patch.dict(settings.FEATURES, {'ENABLE_NEW_DASHBOARD': True})
    def setUp(self):
        super(StudentProfileViewTest, self).setUp()

        # Create/activate a new account
        activation_key = account_api.create_account(self.USERNAME, self.PASSWORD, self.EMAIL)
        account_api.activate_account(activation_key)

        # Login
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result)

    def test_index(self):
        response = self.client.get(reverse('profile_index'))
        self.assertContains(response, "Student Profile")
        self.assertContains(response, "Connected Accounts")

    def test_name_change(self):
        # Verify that the name on the account is blank
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEqual(profile_info['full_name'], '')

        response = self._change_name(self.FULL_NAME)
        self.assertEqual(response.status_code, 204)

        # Verify that the name on the account has been changed
        profile_info = profile_api.profile_info(self.USERNAME)
        self.assertEqual(profile_info['full_name'], self.FULL_NAME)

    def test_name_change_invalid(self):
        # Name cannot be an empty string
        response = self._change_name('')
        self.assertEqual(response.status_code, 400)

    def test_name_change_missing_params(self):
        response = self._change_name(None)
        self.assertEqual(response.status_code, 400)

    @patch('student_profile.views.profile_api.update_profile')
    def test_name_change_internal_error(self, mock_update_profile):
        # This can't happen if the user is logged in, but test it anyway
        mock_update_profile.side_effect = profile_api.ProfileUserNotFound
        response = self._change_name(self.FULL_NAME)
        self.assertEqual(response.status_code, 500)

    @patch('student_profile.views.language_api.preferred_language')
    @patch('student_profile.views.language_api.released_languages')
    def test_get_released_languages(self, mock_released_languages, mock_preferred_language):
        mock_released_languages.return_value = [self.TEST_LANGUAGE]
        mock_preferred_language.return_value = self.TEST_LANGUAGE

        response = self.client.get(reverse('language_info'))
        self.assertEqual(
            json.loads(response.content),
            {
                'preferredLanguage': {'code': self.TEST_LANGUAGE.code, 'name': self.TEST_LANGUAGE.name},
                'languages': [{'code': self.TEST_LANGUAGE.code, 'name': self.TEST_LANGUAGE.name}]
            }
        )

    @patch('student_profile.views.language_api.released_languages')
    def test_language_change(self, mock_released_languages):
        mock_released_languages.return_value = [self.TEST_LANGUAGE]

        # Set the dummy language as the user's preferred language
        response = self._change_preferences(language=self.TEST_LANGUAGE.code)
        self.assertEqual(response.status_code, 204)

        # Verify that the dummy language is now the user's preferred language
        preferences = profile_api.preference_info(self.USERNAME)
        self.assertEqual(preferences[LANGUAGE_KEY], self.TEST_LANGUAGE.code)

        # Verify that the page reloads in the dummy language
        response = self.client.get(reverse('profile_index'))
        self.assertContains(response, u"Stüdént Pröfïlé")

    @ddt.data(*INVALID_LANGUAGE_CODES)
    def test_change_to_invalid_or_unreleased_language(self, language_code):
        response = self._change_preferences(language=language_code)
        self.assertEqual(response.status_code, 400)

    def test_change_to_missing_language(self):
        response = self._change_preferences(language=None)
        self.assertEqual(response.status_code, 400)

    @patch('student_profile.views.profile_api.update_preferences')
    @patch('student_profile.views.language_api.released_languages')
    def test_language_change_missing_profile(self, mock_released_languages, mock_update_preferences):
        # This can't happen if the user is logged in, but test it anyway
        mock_released_languages.return_value = [self.TEST_LANGUAGE]
        mock_update_preferences.side_effect = profile_api.ProfileUserNotFound

        response = self._change_preferences(language=self.TEST_LANGUAGE.code)
        self.assertEqual(response.status_code, 500)

    @ddt.data(
        ('get', 'profile_index'),
        ('put', 'profile_index'),
        ('put', 'preference_handler'),
        ('get', 'language_info'),
    )
    @ddt.unpack
    def test_require_login(self, method, url_name):
        # Access the page while logged out
        self.client.logout()
        url = reverse(url_name)
        response = getattr(self.client, method)(url, follow=True)

        # Should have been redirected to the login page
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn('accounts/login?next=', response.redirect_chain[0][0])

    @ddt.data(
        (['get', 'put'], 'profile_index'),
        (['put'], 'preference_handler'),
        (['get'], 'language_info'),
    )
    @ddt.unpack
    def test_require_http_method(self, correct_methods, url_name):
        wrong_methods = {'get', 'put', 'post', 'head', 'options', 'delete'} - set(correct_methods)
        url = reverse(url_name)

        for method in wrong_methods:
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 405)

    def _change_name(self, new_name):
        """Request a name change.

        Returns:
            HttpResponse

        """
        data = {}
        if new_name is not None:
            # We can't pass a Unicode object to urlencode, so we encode the Unicode object
            data['fullName'] = new_name.encode('utf-8')

        return self.client.put(
            path=reverse('profile_index'),
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )

    def _change_preferences(self, **preferences):
        """Request a change to the user's preferences.

        Returns:
            HttpResponse

        """
        data = {}
        for key, value in preferences.iteritems():
            if value is not None:
                data[key] = value

        return self.client.put(
            path=reverse('preference_handler'),
            data=urlencode(data),
            content_type='application/x-www-form-urlencoded'
        )
