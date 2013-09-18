"""
Tests of XML export
"""

from datetime import datetime, timedelta, tzinfo
from tempfile import mkdtemp
import unittest
import shutil
from textwrap import dedent
import mock

import pytz
from fs.osfs import OSFS
from path import path

from xmodule.modulestore import Location
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.xml_exporter import EdxJSONEncoder
from xmodule.tests import DATA_DIR


def strip_filenames(descriptor):
    """
    Recursively strips 'filename' from all children's definitions.
    """
    print("strip filename from {desc}".format(desc=descriptor.location.url()))
    if descriptor._field_data.has(descriptor, 'filename'):
        descriptor._field_data.delete(descriptor, 'filename')

    if hasattr(descriptor, 'xml_attributes'):
        if 'filename' in descriptor.xml_attributes:
            del descriptor.xml_attributes['filename']

    for d in descriptor.get_children():
        strip_filenames(d)

    descriptor.save()


class RoundTripTestCase(unittest.TestCase):
    """
    Check that our test courses roundtrip properly.
    Same course imported , than exported, then imported again.
    And we compare original import with second import (after export).
    Thus we make sure that export and import work properly.
    """

    @mock.patch('xmodule.course_module.requests.get')
    def check_export_roundtrip(self, data_dir, course_dir, mock_get):

        # Patch network calls to retrieve the textbook TOC
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        root_dir = path(self.temp_dir)
        print("Copying test course to temp dir {0}".format(root_dir))

        data_dir = path(data_dir)
        shutil.copytree(data_dir / course_dir, root_dir / course_dir)

        print("Starting import")
        initial_import = XMLModuleStore(root_dir, course_dirs=[course_dir])

        courses = initial_import.get_courses()
        self.assertEquals(len(courses), 1)
        initial_course = courses[0]

        # export to the same directory--that way things like the custom_tags/ folder
        # will still be there.
        print("Starting export")
        fs = OSFS(root_dir)
        export_fs = fs.makeopendir(course_dir)

        xml = initial_course.export_to_xml(export_fs)
        with export_fs.open('course.xml', 'w') as course_xml:
            course_xml.write(xml)

        print("Starting second import")
        second_import = XMLModuleStore(root_dir, course_dirs=[course_dir])

        courses2 = second_import.get_courses()
        self.assertEquals(len(courses2), 1)
        exported_course = courses2[0]

        print("Checking course equality")

        # HACK: filenames change when changing file formats
        # during imports from old-style courses.  Ignore them.
        strip_filenames(initial_course)
        strip_filenames(exported_course)

        self.assertEquals(initial_course, exported_course)
        self.assertEquals(initial_course.id, exported_course.id)
        course_id = initial_course.id

        print("Checking key equality")
        self.assertEquals(sorted(initial_import.modules[course_id].keys()),
                          sorted(second_import.modules[course_id].keys()))

        print("Checking module equality")
        for location in initial_import.modules[course_id].keys():
            print("Checking", location)
            self.assertEquals(initial_import.modules[course_id][location],
                              second_import.modules[course_id][location])

    def setUp(self):
        self.maxDiff = None
        self.temp_dir = mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def test_toy_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "toy")

    def test_simple_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "simple")

    def test_conditional_and_poll_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "conditional_and_poll")

    def test_selfassessment_roundtrip(self):
        #Test selfassessment xmodule to see if it exports correctly
        self.check_export_roundtrip(DATA_DIR, "self_assessment")

    def test_graphicslidertool_roundtrip(self):
        #Test graphicslidertool xmodule to see if it exports correctly
        self.check_export_roundtrip(DATA_DIR, "graphic_slider_tool")

    def test_exam_registration_roundtrip(self):
        # Test exam_registration xmodule to see if it exports correctly
        self.check_export_roundtrip(DATA_DIR, "test_exam_registration")

    def test_word_cloud_roundtrip(self):
        self.check_export_roundtrip(DATA_DIR, "word_cloud")


class TestEdxJsonEncoder(unittest.TestCase):
    """
    Tests for xml_exporter.EdxJSONEncoder
    """
    def setUp(self):
        self.encoder = EdxJSONEncoder()

        class OffsetTZ(tzinfo):
            """A timezone with non-None utcoffset"""
            def utcoffset(self, _dt):
                return timedelta(hours=4)

        self.offset_tz = OffsetTZ()

        class NullTZ(tzinfo):
            """A timezone with None as its utcoffset"""
            def utcoffset(self, _dt):
                return None
        self.null_utc_tz = NullTZ()

    def test_encode_location(self):
        loc = Location('i4x', 'org', 'course', 'category', 'name')
        self.assertEqual(loc.url(), self.encoder.default(loc))

        loc = Location('i4x', 'org', 'course', 'category', 'name', 'version')
        self.assertEqual(loc.url(), self.encoder.default(loc))

    def test_encode_naive_datetime(self):
        self.assertEqual(
            "2013-05-03T10:20:30.000100",
            self.encoder.default(datetime(2013, 5, 3, 10, 20, 30, 100))
        )
        self.assertEqual(
            "2013-05-03T10:20:30",
            self.encoder.default(datetime(2013, 5, 3, 10, 20, 30))
        )

    def test_encode_utc_datetime(self):
        self.assertEqual(
            "2013-05-03T10:20:30+00:00",
            self.encoder.default(datetime(2013, 5, 3, 10, 20, 30, 0, pytz.UTC))
        )

        self.assertEqual(
            "2013-05-03T10:20:30+04:00",
            self.encoder.default(datetime(2013, 5, 3, 10, 20, 30, 0, self.offset_tz))
        )

        self.assertEqual(
            "2013-05-03T10:20:30Z",
            self.encoder.default(datetime(2013, 5, 3, 10, 20, 30, 0, self.null_utc_tz))
        )

    def test_fallthrough(self):
        with self.assertRaises(TypeError):
            self.encoder.default(None)

        with self.assertRaises(TypeError):
            self.encoder.default({})
