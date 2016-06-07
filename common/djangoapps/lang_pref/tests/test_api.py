# -*- coding: utf-8 -*-
""" Tests for the language API. """

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import translation
from lang_pref import api as language_api


class LanguageApiTest(TestCase):

    def test_released_languages(self):
        released_languages = language_api.released_languages()
        self.assertGreaterEqual(len(released_languages), 1)

    @override_settings(ALL_LANGUAGES=[[u"cs", u"Czech"], [u"nl", u"Dutch"]])
    def test_all_languages(self):
        with translation.override('fr'):
            all_languages = language_api.all_languages()

        self.assertEqual(2, len(all_languages))
        self.assertLess(all_languages[0][1], all_languages[1][1])
        self.assertEqual("nl", all_languages[0][0])
        self.assertEqual("cs", all_languages[1][0])
        self.assertEqual(u"Hollandais", all_languages[0][1])
        self.assertEqual(u"Tchèque", all_languages[1][1])
