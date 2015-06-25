"""
Tests i18n in courseware
"""
import re

from django.test import TestCase
from django.test.utils import override_settings


@override_settings(LANGUAGES=(('eo', 'Esperanto'),))
class I18nTestCase(TestCase):
    """
    Tests for i18n
    """
    def test_default_is_en(self):
        response = self.client.get('/')
        self.assertIn('<html lang="en">', response.content)
        self.assertEqual(response['Content-Language'], 'en')
        self.assertTrue(re.search('<body.*class=".*lang_en">', response.content))

    def test_esperanto(self):
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='eo')
        self.assertIn('<html lang="eo">', response.content)
        self.assertEqual(response['Content-Language'], 'eo')
        self.assertTrue(re.search('<body.*class=".*lang_eo">', response.content))
