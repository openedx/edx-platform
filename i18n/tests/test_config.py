import os
from unittest import TestCase

from i18n.config import Configuration, LOCALE_DIR, CONFIGURATION

class TestConfiguration(TestCase):
    """
    Tests functionality of i18n/config.py
    """

    def test_config(self):
        config_filename = os.path.normpath(os.path.join(LOCALE_DIR, 'config.yaml'))
        config = Configuration(config_filename)
        self.assertEqual(config.source_locale, 'en')

    def test_no_config(self):
        config_filename = os.path.normpath(os.path.join(LOCALE_DIR, 'no_such_file'))
        with self.assertRaises(Exception):
            Configuration(config_filename)

    def test_valid_configuration(self):
        """
        Make sure we have a valid configuration file,
        and that it contains an 'en' locale.
        Also check values of dummy_locale and source_locale.
        """
        self.assertIsNotNone(CONFIGURATION)
        locales = CONFIGURATION.locales
        self.assertIsNotNone(locales)
        self.assertIsInstance(locales, list)
        self.assertIn('en', locales)
        self.assertEqual('eo', CONFIGURATION.dummy_locales[0])
        self.assertEqual('en', CONFIGURATION.source_locale)
