from datetime import datetime, timedelta
import os
from unittest import TestCase

from nose.plugins.skip import SkipTest
import polib
from pytz import UTC

from i18n import extract
from i18n.config import CONFIGURATION

# Make sure setup runs only once
SETUP_HAS_RUN = False


class TestExtract(TestCase):
    """
    Tests functionality of i18n/extract.py
    """
    generated_files = ('django-partial.po', 'djangojs-partial.po', 'mako.po')

    def setUp(self):
        # Skip this test because it takes too long (>1 minute)
        # TODO: figure out how to declare a "long-running" test suite
        # and add this test to it.
        raise SkipTest()

        global SETUP_HAS_RUN

        # Subtract 1 second to help comparisons with file-modify time succeed,
        # since os.path.getmtime() is not millisecond-accurate
        self.start_time = datetime.now(UTC) - timedelta(seconds=1)
        super(TestExtract, self).setUp()
        if not SETUP_HAS_RUN:
            # Run extraction script. Warning, this takes 1 minute or more
            extract.main(verbosity=0)
            SETUP_HAS_RUN = True

    def get_files(self):
        """
        This is a generator.
        Returns the fully expanded filenames for all extracted files
        Fails assertion if one of the files doesn't exist.
        """
        for filename in self.generated_files:
            path = os.path.join(CONFIGURATION.source_messages_dir, filename)
            exists = os.path.exists(path)
            self.assertTrue(exists, msg='Missing file: %s' % filename)
            if exists:
                yield path

    def test_files(self):
        """
        Asserts that each auto-generated file has been modified since 'extract' was launched.
        Intended to show that the file has been touched by 'extract'.
        """

        for path in self.get_files():
            self.assertTrue(datetime.fromtimestamp(os.path.getmtime(path)) > self.start_time,
                            msg='File not recently modified: %s' % os.path.basename(path))

    def test_is_keystring(self):
        """
        Verifies is_keystring predicate
        """
        entry1 = polib.POEntry()
        entry2 = polib.POEntry()
        entry1.msgid = "_.lms.admin.warning.keystring"
        entry2.msgid = "This is not a keystring"
        self.assertTrue(extract.is_key_string(entry1.msgid))
        self.assertFalse(extract.is_key_string(entry2.msgid))

    def test_headers(self):
        """Verify all headers have been modified"""
        for path in self.get_files():
            po = polib.pofile(path)
            header = po.header
            self.assertEqual(
                header.find('edX translation file'),
                0,
                msg='Missing header in %s:\n"%s"' % (os.path.basename(path), header)
            )

    def test_metadata(self):
        """Verify all metadata has been modified"""
        for path in self.get_files():
            po = polib.pofile(path)
            metadata = po.metadata
            value = metadata['Report-Msgid-Bugs-To']
            expected = 'openedx-translation@googlegroups.com'
            self.assertEquals(expected, value)
