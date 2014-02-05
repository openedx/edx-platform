"""
Test that the compiled .mo files match the translations in the
uncompiled .po files.

This is required because we are checking in the .mo files into
the repo, but compiling them is a manual process. We want to make
sure that we find out if someone forgets the compilation step.
"""

import ddt
import polib
from unittest import TestCase

from i18n.config import CONFIGURATION, LOCALE_DIR

@ddt.ddt
class TestCompiledMessages(TestCase):
    """
    Test that mo files match their source po files
    """

    PO_FILES = ['django.po', 'djangojs.po']

    @ddt.data(*CONFIGURATION.translated_locales)
    def test_translated_messages(self, locale):
        message_dir = LOCALE_DIR / locale / 'LC_MESSAGES'
        for pofile_name in self.PO_FILES:
            pofile_path = message_dir / pofile_name
            pofile = polib.pofile(pofile_path)
            mofile = polib.mofile(pofile_path.stripext() + '.mo')

            po_entries = {entry.msgid: entry for entry in pofile.translated_entries()}
            mo_entries = {entry.msgid: entry for entry in mofile.translated_entries()}

            # Check that there are no entries in po that aren't in mo, and vice-versa
            self.assertEquals(po_entries.viewkeys(), mo_entries.viewkeys())

            for entry_id, po_entry in po_entries.iteritems():
                mo_entry = mo_entries[entry_id]
                for attr in ('msgstr', 'msgid_plural', 'msgstr_plural', 'msgctxt', 'obsolete', 'encoding'):
                    po_attr = getattr(po_entry, attr)
                    mo_attr = getattr(mo_entry, attr)

                    # The msgstr_plural in the mo_file is keyed on ints, but in the po_file it's
                    # keyed on strings. This normalizes them.
                    if attr == 'msgstr_plural':
                        po_attr = {int(key): val for (key, val) in po_attr.items()}

                    self.assertEquals(
                        po_attr,
                        mo_attr,
                        "When comparing {} for entry {!r}, {!r} from the .po file doesn't match {!r} from the .mo file".format(
                            attr,
                            entry_id,
                            po_attr,
                            mo_attr,
                        )
                    )
