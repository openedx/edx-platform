# -*- coding: utf-8 -*-
""" Tests for the language API. """

from django.test import TestCase
from lang_pref import api as language_api


class LanguageApiTest(TestCase):

    def test_released_languages(self):
        released_languages = language_api.released_languages()
        self.assertGreaterEqual(len(released_languages), 1)
