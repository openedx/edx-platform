"""
This test tests that i18n extraction (`paver i18n_extract -v`) works properly.
"""
from datetime import datetime, timedelta
import os
import random
import re
import sys
import string
import subprocess
from unittest import TestCase

from mock import patch
from polib import pofile
from pytz import UTC

from i18n import extract
from i18n import generate
from i18n import dummy
from i18n.config import CONFIGURATION


class TestGenerate(TestCase):
    """
    Tests functionality of i18n/generate.py
    """
    generated_files = ('django-partial.po', 'djangojs-partial.po', 'mako.po')

    @classmethod
    def setUpClass(cls):
        super(TestGenerate, cls).setUpClass()

        sys.stderr.write(
            "\nThis test tests that i18n extraction (`paver i18n_extract`) works properly. "
            "If you experience failures, please check that all instances of `gettext` and "
            "`ngettext` are used correctly. You can also try running `paver i18n_extract -v` "
            "locally for more detail.\n"
        )
        sys.stderr.write(
            "\nExtracting i18n strings and generating dummy translations; "
            "this may take a few minutes\n"
        )
        sys.stderr.flush()
        extract.main(verbose=2)
        dummy.main(verbose=2)

    @classmethod
    def tearDownClass(cls):
        # Clear the Esperanto & RTL directories of any test artifacts
        cmd = "git checkout conf/locale/eo conf/locale/rtl"
        sys.stderr.write("Cleaning up dummy language directories: " + cmd)
        sys.stderr.flush()
        returncode = subprocess.call(cmd, shell=True)
        assert returncode == 0
        super(TestGenerate, cls).tearDownClass()

    def setUp(self):
        super(TestGenerate, self).setUp()

        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now(UTC) - timedelta(seconds=1)

    def test_merge(self):
        """
        Tests merge script on English source files.
        """
        filename = os.path.join(CONFIGURATION.source_messages_dir, random_name())
        generate.merge(CONFIGURATION.source_locale, target=filename)
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    # Patch dummy_locales to not have esperanto present
    @patch.object(CONFIGURATION, 'dummy_locales', ['fake2'])
    def test_main(self):
        """
        Runs generate.main() which should merge source files,
        then compile all sources in all configured languages.
        Validates output by checking all .mo files in all configured languages.
        .mo files should exist, and be recently created (modified
        after start of test suite)
        """
        generate.main(verbosity=0, strict=False)
        for locale in CONFIGURATION.translated_locales:
            for filename in ('django', 'djangojs'):
                mofile = filename + '.mo'
                path = os.path.join(CONFIGURATION.get_messages_dir(locale), mofile)
                exists = os.path.exists(path)
                self.assertTrue(exists, msg='Missing file in locale %s: %s' % (locale, mofile))
                self.assertGreaterEqual(
                    datetime.fromtimestamp(os.path.getmtime(path), UTC),
                    self.start_time,
                    msg='File not recently modified: %s' % path
                )
            # Segmenting means that the merge headers don't work they way they
            # used to, so don't make this check for now. I'm not sure if we'll
            # get the merge header back eventually, or delete this code eventually.
            # self.assert_merge_headers(locale)

    def assert_merge_headers(self, locale):
        """
        This is invoked by test_main to ensure that it runs after
        calling generate.main().

        There should be exactly three merge comment headers
        in our merged .po file. This counts them to be sure.
        A merge comment looks like this:
        # #-#-#-#-#  django-partial.po (0.1a)  #-#-#-#-#

        """
        path = os.path.join(CONFIGURATION.get_messages_dir(locale), 'django.po')
        pof = pofile(path)
        pattern = re.compile('^#-#-#-#-#', re.M)
        match = pattern.findall(pof.header)
        self.assertEqual(
            len(match),
            3,
            msg="Found %s (should be 3) merge comments in the header for %s" % (len(match), path)
        )


def random_name(size=6):
    """Returns random filename as string, like test-4BZ81W"""
    chars = string.ascii_uppercase + string.digits
    return 'test-' + ''.join(random.choice(chars) for x in range(size))
