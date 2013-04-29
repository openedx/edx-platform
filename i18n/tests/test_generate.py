import os, string, random
from unittest import TestCase
from datetime import datetime, timedelta

import generate
from execute import get_config, messages_dir, SOURCE_MSGS_DIR, SOURCE_LOCALE

class TestGenerate(TestCase):
    """
    Tests functionality of i18n/generate.py
    """
    generated_files = ('django-partial.po', 'djangojs.po', 'mako.po')

    def setUp(self):
        self.configuration = get_config()

        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now() - timedelta(seconds=1)

    def test_configuration(self):
        """
        Make sure we have a valid configuration file,
        and that it contains an 'en' locale.
        """
        self.assertIsNotNone(self.configuration)
        locales = self.configuration['locales']
        self.assertIsNotNone(locales)
        self.assertIsInstance(locales, list)
        self.assertIn('en', locales)

    def test_merge(self):
        """
        Tests merge script on English source files.
        """
        filename = os.path.join(SOURCE_MSGS_DIR, random_name())
        generate.merge(SOURCE_LOCALE, target=filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    def test_main(self):
        """
        Runs generate.main() which should merge source files,
        then compile all sources in all configured languages.
        Validates output by checking all .mo files in all configured languages.
        .mo files should exist, and be recently created (modified
        after start of test suite)
        """
        generate.main()
        for locale in self.configuration['locales']:
            for filename in ('django.mo', 'djangojs.mo'):
                path = os.path.join(messages_dir(locale), filename)
                exists = os.path.exists(path)
                self.assertTrue(exists, msg='Missing file in locale %s: %s' % (locale, filename))
                self.assertTrue(datetime.fromtimestamp(os.path.getmtime(path)) >= self.start_time,
                                msg='File not recently modified: %s' % path)

def random_name(size=6):
    """Returns random filename as string, like test-4BZ81W"""
    chars = string.ascii_uppercase + string.digits
    return 'test-' + ''.join(random.choice(chars) for x in range(size))
