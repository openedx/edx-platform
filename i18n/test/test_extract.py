import os
from unittest import TestCase
from datetime import datetime
import polib

import extract
from execute import SOURCE_MSGS_DIR

class TestExtract(TestCase):
    """
    Tests functionality of i18n/extract.py
    """
    generated_files = ('django.po', 'djangojs.po', 'mako.po')

    def setUp(self):
        self.start_time = datetime.now()
        extract.main()

    def get_files (self):
        """
        This is a generator.
        Returns the fully expanded filenames for all extracted files
        Fails assertion if one of the files doesn't exist.
        """
        for filename in self.generated_files:
            path = os.path.join(SOURCE_MSGS_DIR, filename)
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
            self.assertEqual(header.find('edX translation file'), 0,
                             msg='Missing header in %s:\n"%s"' % \
                             (os.path.basename(path), header))

    def test_metadata(self):
        """Verify all metadata has been modified"""
        for path in self.get_files():    
            po = polib.pofile(path)
            metadata = po.metadata
            value = metadata['Report-Msgid-Bugs-To']
            expected = 'translation_team@edx.org'
            self.assertEquals(expected, value)
