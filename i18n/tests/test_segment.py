"""Test i18n/segment.py"""

import os.path
import shutil
import unittest

from path import path
import polib

from i18n.segment import segment_pofile


HERE = path(__file__).dirname()
TEST_DATA = HERE / "data"
WORK = HERE / "work"


class SegmentTest(unittest.TestCase):
    """Test segment_pofile."""

    def setUp(self):
        if not os.path.exists(WORK):
            os.mkdir(WORK)
        self.addCleanup(shutil.rmtree, WORK)

    def assert_pofile_same(self, pofile1, pofile2):
        """The paths `p1` and `p2` should be identical pofiles."""
        po1 = polib.pofile(pofile1)
        po2 = polib.pofile(pofile2)
        self.assertEqual(po1, po2)

    def test_sample_data(self):
        work_file = WORK / "django.po"
        shutil.copyfile(TEST_DATA / "django_before.po", work_file)
        original_pofile = polib.pofile(work_file)

        written = segment_pofile(
            work_file,
            {
                'studio.po': [
                    'cms/*',
                    'other_cms/*',
                ],
            }
        )

        self.assertEqual(written, set([WORK / "django.po", WORK / "studio.po"]))

        pofiles = [polib.pofile(f) for f in written]
        after_entries = sum(len(pofile) for pofile in pofiles)
        self.assertEqual(len(original_pofile), after_entries)

        original_ids = set(m.msgid for m in original_pofile)
        after_ids = set(m.msgid for pofile in pofiles for m in pofile)
        self.assertEqual(original_ids, after_ids)

        self.assert_pofile_same(WORK / "django.po", TEST_DATA / "django_after.po")
        self.assert_pofile_same(WORK / "studio.po", TEST_DATA / "studio.po")
