# -*- coding: utf-8 -*-
"""
This test file will verify proper password policy enforcement, which is an option feature
"""
import json
import uuid

from django.test import TestCase
from django.core.urlresolvers import reverse
from mock import patch
from django.test.utils import override_settings


@patch.dict("django.conf.settings.FEATURES", {'USE_PASSWORD_POLICY_ENFORCEMENT': True})
class TestPasswordPolicy(TestCase):
    """
    Go through some password policy tests to make sure things are properly working
    """

    def check_for_post_code(self, code, url, data={}):
            """
            Check that we got the expected code when accessing url via POST.
            Returns the HTTP response.
            `self` is a class that subclasses TestCase.

            `code` is a status code for HTTP responses.

            `url` is a url pattern for which we want to test the response.
            """
            resp = self.client.post(url, data)
            self.assertEqual(resp.status_code, code,
                             "got code %d for url '%s'. Expected code %d"
                             % (resp.status_code, url, code))
            return resp

    def _do_register_attempt(self, username, email, password):
        """
        Helper method to make the call to the do registration
        """
        resp = self.check_for_post_code(200, reverse('create_account'), {
            'username': username,
            'email': email,
            'password': password,
            'name': 'username',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        data = json.loads(resp.content)
        return data

    def _get_unique_username(self):
        """
        Generate a random username
        """
        return 'foo_bar' + uuid.uuid4().hex

    def _get_unique_email(self):
        """
        Generate a random email address
        """
        return 'foo' + uuid.uuid4().hex + '@bar.com'

    @override_settings(PASSWORD_MIN_LENGTH=6)
    def test_password_length(self):
        """
        Assert that a too short password will fail and a good length one will pass
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'aaa'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Invalid Length (must be 6 characters or more)")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'ThisIsALongerPassword'
        )
        self.assertEqual(data['success'], True)

    @override_settings(PASSWORD_MAX_LENGTH=12)
    def test_bad_too_long_password(self):
        """
        Assert that a password that is too long will fail
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'ThisPasswordIsWayTooLong'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Invalid Length (must be 12 characters or less)")

    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'UPPER': 3})
    def test_enough_upper_case_letters(self):
        """
        Assert the rules regarding minimum upper case letters in a password
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'thisshouldfail'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Must be more complex (must contain 3 or more uppercase characters)")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'ThisShouldPass'
        )
        self.assertEqual(data['success'], True)

    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'LOWER': 3})
    def test_enough_lower_case_letters(self):
        """
        Assert the rules regarding minimum lower case letters in a password
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'THISSHOULDFAIL'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Must be more complex (must contain 3 or more lowercase characters)")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'ThisShouldPass'
        )
        self.assertEqual(data['success'], True)

    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'DIGITS': 3})
    def test_enough_digits(self):
        """
        Assert the rules regarding minimum lower case letters in a password
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'thishasnodigits'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Must be more complex (must contain 3 or more digits)")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'Th1sSh0uldPa88'
        )
        self.assertEqual(data['success'], True)

    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'PUNCTUATION': 3})
    def test_enough_punctuations(self):
        """
        Assert the rules regarding minimum punctuation count in a password
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'thisshouldfail'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Must be more complex (must contain 3 or more punctuation characters)")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'Th!sSh.uldPa$*'
        )
        print 'result = {0}'.format(data)
        self.assertEqual(data['success'], True)

    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'WORDS': 3})
    def test_enough_words(self):
        """
        Assert the rules regarding minimum word count in password
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'thisshouldfail'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Must be more complex (must contain 3 or more unique words)")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            u'this should pass'
        )
        self.assertEqual(data['success'], True)

    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'PUNCTUATION': 3})
    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'WORDS': 3})
    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'DIGITS': 3})
    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'LOWER': 3})
    @patch.dict("django.conf.settings.PASSWORD_COMPLEXITY", {'UPPER': 3})
    def test_multiple_errors(self):
        """
        Make sure we assert against all violations
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'thisshouldfail'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(
            data['value'],
            "Password: Must be more complex ("
            "must contain 3 or more uppercase characters, "
            "must contain 3 or more digits, "
            "must contain 3 or more punctuation characters, "
            "must contain 3 or more unique words"
            ")"
        )

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            u'tH1s Sh0u!d P3#$'
        )
        self.assertEqual(data['success'], True)

    @override_settings(PASSWORD_DICTIONARY=['foo', 'bar'])
    @override_settings(PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD=1)
    def test_dictionary_similarity(self):
        """
        Assert that passwords should not be too similar to a set of words
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'foo'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Too similar to a restricted dictionary word.")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'bar'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Too similar to a restricted dictionary word.")

        # try one that is just one character different from the restricted dictionary
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            'fo0'
        )
        self.assertEqual(data['success'], False)
        self.assertEqual(data['value'], "Password: Too similar to a restricted dictionary word.")

        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            u'this_is_ok'
        )
        self.assertEqual(data['success'], True)

    def test_with_unicode(self):
        """
        Make sure the library we are using is OK with unicode characters
        """
        data = self._do_register_attempt(
            self._get_unique_username(),
            self._get_unique_email(),
            u'四節比分和七年前'
        )
        self.assertEqual(data['success'], True)
