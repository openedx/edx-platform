# -*- coding: utf-8 -*-
""" Tests for the language API. """

from django.test import TestCase
import ddt

from lang_pref import api as language_api


@ddt.ddt
class LanguageApiTest(TestCase):

    INVALID_LANGUAGE_CODES = ['', 'foo']

    def test_released_languages(self):
        released_languages = language_api.released_languages()
        self.assertGreaterEqual(len(released_languages), 1)

    def test_preferred_language(self):
        preferred_language = language_api.preferred_language('fr')
        self.assertEqual(preferred_language, u'Français')

    @ddt.data(*INVALID_LANGUAGE_CODES)
    def test_invalid_preferred_language(self, language_code):
        preferred_language = language_api.preferred_language(language_code)
        self.assertEqual(preferred_language, u'English')

    def test_no_preferred_language(self):
        preferred_language = language_api.preferred_language(None)
        self.assertEqual(preferred_language, u'English')
