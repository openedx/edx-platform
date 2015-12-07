"""
Tests of XML export
"""

import ddt
import lxml.etree
import mock
import os
import pytz
import shutil
import tarfile
import unittest
import uuid

from datetime import datetime, timedelta, tzinfo
from fs.osfs import OSFS
from path import Path as path
from tempfile import mkdtemp
from textwrap import dedent

from xblock.core import XBlock
from xblock.fields import String, Scope, Integer
from xblock.test.tools import blocks_are_equivalent

from opaque_keys.edx.locations import Location
from xmodule.modulestore import EdxJSONEncoder
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.modulestore.xml_exporter import (
    convert_between_versions, get_version
)
from xmodule.tests import DATA_DIR
from xmodule.tests.helpers import directories_equal
from xmodule.x_module import XModuleMixin


def strip_filenames(descriptor):
    """
    Recursively strips 'filename' from all children's definitions.
    """
    print "strip filename from {desc}".format(desc=descriptor.location.to_deprecated_string())
    if descriptor._field_data.has(descriptor, 'filename'):
        descriptor._field_data.delete(descriptor, 'filename')

    if hasattr(descriptor, 'xml_attributes'):
        if 'filename' in descriptor.xml_attributes:
            del descriptor.xml_attributes['filename']

    for child in descriptor.get_children():
        strip_filenames(child)

    descriptor.save()


class PureXBlock(XBlock):

    """Class for testing pure XBlocks."""

    has_children = True
    field1 = String(default="something", scope=Scope.user_state)
    field2 = Integer(scope=Scope.user_state)


@ddt.ddt
class RoundTripTestCase(unittest.TestCase):
    """
    Check that our test courses roundtrip properly.
    Same course imported , than exported, then imported again.
    And we compare original import with second import (after export).
    Thus we make sure that export and import work properly.
    """

    def setUp(self):
        super(RoundTripTestCase, self).setUp()
        self.maxDiff = None
        self.temp_dir = mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

    @mock.patch('xmodule.course_module.requests.get')
    @ddt.data(
        "toy",
        "simple",
        "conditional_and_poll",
        "conditional",
        "self_assessment",
        "graphic_slider_tool",
        "test_exam_registration",
        "word_cloud",
        "pure_xblock",
    )
    @XBlock.register_temp_plugin(PureXBlock, 'pure')
    def test_export_roundtrip(self, course_dir, mock_get):

        # Patch network calls to retrieve the textbook TOC
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        root_dir = path(self.temp_dir)
        print "Copying test course to temp dir {0}".format(root_dir)

        data_dir = path(DATA_DIR)
        shutil.copytree(data_dir / course_dir, root_dir / course_dir)

        print "Starting import"
        initial_import = XMLModuleStore(root_dir, source_dirs=[course_dir], xblock_mixins=(XModuleMixin,))

        courses = initial_import.get_courses()
        self.assertEquals(len(courses), 1)
        initial_course = courses[0]

        # export to the same directory--that way things like the custom_tags/ folder
        # will still be there.
        print "Starting export"
        file_system = OSFS(root_dir)
        initial_course.runtime.export_fs = file_system.makeopendir(course_dir)
        root = lxml.etree.Element('root')

        initial_course.add_xml_to_node(root)
        with initial_course.runtime.export_fs.open('course.xml', 'w') as course_xml:
            lxml.etree.ElementTree(root).write(course_xml)

        print "Starting second import"
        second_import = XMLModuleStore(root_dir, source_dirs=[course_dir], xblock_mixins=(XModuleMixin,))

        courses2 = second_import.get_courses()
        self.assertEquals(len(courses2), 1)
        exported_course = courses2[0]

        print "Checking course equality"

        # HACK: filenames change when changing file formats
        # during imports from old-style courses.  Ignore them.
        strip_filenames(initial_course)
        strip_filenames(exported_course)

        self.assertTrue(blocks_are_equivalent(initial_course, exported_course))
        self.assertEquals(initial_course.id, exported_course.id)
        course_id = initial_course.id

        print "Checking key equality"
        self.assertItemsEqual(
            initial_import.modules[course_id].keys(),
            second_import.modules[course_id].keys()
        )

        print "Checking module equality"
        for location in initial_import.modules[course_id].keys():
            print("Checking", location)
            self.assertTrue(blocks_are_equivalent(
                initial_import.modules[course_id][location],
                second_import.modules[course_id][location]
            ))


class TestEdxJsonEncoder(unittest.TestCase):
    """
    Tests for xml_exporter.EdxJSONEncoder
    """
    def setUp(self):
        super(TestEdxJsonEncoder, self).setUp()

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
        loc = Location('org', 'course', 'run', 'category', 'name', None)
        self.assertEqual(loc.to_deprecated_string(), self.encoder.default(loc))

        loc = Location('org', 'course', 'run', 'category', 'name', 'version')
        self.assertEqual(loc.to_deprecated_string(), self.encoder.default(loc))

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


class ConvertExportFormat(unittest.TestCase):
    """
    Tests converting between export formats.
    """
    def setUp(self):
        """ Common setup. """
        super(ConvertExportFormat, self).setUp()

        # Directory for expanding all the test archives
        self.temp_dir = mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

        # Directory where new archive will be created
        self.result_dir = path(self.temp_dir) / uuid.uuid4().hex
        os.mkdir(self.result_dir)

        # Expand all the test archives and store their paths.
        self.data_dir = path(__file__).realpath().parent / 'data'

        self._version0_nodrafts = None
        self._version1_nodrafts = None
        self._version0_drafts = None
        self._version1_drafts = None
        self._version1_drafts_extra_branch = None
        self._no_version = None

    @property
    def version0_nodrafts(self):
        "lazily expand this"
        if self._version0_nodrafts is None:
            self._version0_nodrafts = self._expand_archive('Version0_nodrafts.tar.gz')
        return self._version0_nodrafts

    @property
    def version1_nodrafts(self):
        "lazily expand this"
        if self._version1_nodrafts is None:
            self._version1_nodrafts = self._expand_archive('Version1_nodrafts.tar.gz')
        return self._version1_nodrafts

    @property
    def version0_drafts(self):
        "lazily expand this"
        if self._version0_drafts is None:
            self._version0_drafts = self._expand_archive('Version0_drafts.tar.gz')
        return self._version0_drafts

    @property
    def version1_drafts(self):
        "lazily expand this"
        if self._version1_drafts is None:
            self._version1_drafts = self._expand_archive('Version1_drafts.tar.gz')
        return self._version1_drafts

    @property
    def version1_drafts_extra_branch(self):
        "lazily expand this"
        if self._version1_drafts_extra_branch is None:
            self._version1_drafts_extra_branch = self._expand_archive('Version1_drafts_extra_branch.tar.gz')
        return self._version1_drafts_extra_branch

    @property
    def no_version(self):
        "lazily expand this"
        if self._no_version is None:
            self._no_version = self._expand_archive('NoVersionNumber.tar.gz')
        return self._no_version

    def _expand_archive(self, name):
        """ Expand archive into a directory and return the directory. """
        target = path(self.temp_dir) / uuid.uuid4().hex
        os.mkdir(target)
        with tarfile.open(self.data_dir / name) as tar_file:
            tar_file.extractall(path=target)

        return target

    def test_no_version(self):
        """ Test error condition of no version number specified. """
        errstring = "unknown version"
        with self.assertRaisesRegexp(ValueError, errstring):
            convert_between_versions(self.no_version, self.result_dir)

    def test_no_published(self):
        """ Test error condition of a version 1 archive with no published branch. """
        errstring = "version 1 archive must contain a published branch"
        no_published = self._expand_archive('Version1_nopublished.tar.gz')
        with self.assertRaisesRegexp(ValueError, errstring):
            convert_between_versions(no_published, self.result_dir)

    def test_empty_course(self):
        """ Test error condition of a version 1 archive with no published branch. """
        errstring = "source archive does not have single course directory at top level"
        empty_course = self._expand_archive('EmptyCourse.tar.gz')
        with self.assertRaisesRegexp(ValueError, errstring):
            convert_between_versions(empty_course, self.result_dir)

    def test_convert_to_1_nodrafts(self):
        """
        Test for converting from version 0 of export format to version 1 in a course with no drafts.
        """
        self._verify_conversion(self.version0_nodrafts, self.version1_nodrafts)

    def test_convert_to_1_drafts(self):
        """
        Test for converting from version 0 of export format to version 1 in a course with drafts.
        """
        self._verify_conversion(self.version0_drafts, self.version1_drafts)

    def test_convert_to_0_nodrafts(self):
        """
        Test for converting from version 1 of export format to version 0 in a course with no drafts.
        """
        self._verify_conversion(self.version1_nodrafts, self.version0_nodrafts)

    def test_convert_to_0_drafts(self):
        """
        Test for converting from version 1 of export format to version 0 in a course with drafts.
        """
        self._verify_conversion(self.version1_drafts, self.version0_drafts)

    def test_convert_to_0_extra_branch(self):
        """
        Test for converting from version 1 of export format to version 0 in a course
        with drafts and an extra branch.
        """
        self._verify_conversion(self.version1_drafts_extra_branch, self.version0_drafts)

    def test_equality_function(self):
        """
        Check equality function returns False for unequal directories.
        """
        self.assertFalse(directories_equal(self.version1_nodrafts, self.version0_nodrafts))
        self.assertFalse(directories_equal(self.version1_drafts_extra_branch, self.version1_drafts))

    def test_version_0(self):
        """
        Check that get_version correctly identifies a version 0 archive (old format).
        """
        self.assertEqual(0, self._version_test(self.version0_nodrafts))

    def test_version_1(self):
        """
        Check that get_version correctly identifies a version 1 archive (new format).
        """
        self.assertEqual(1, self._version_test(self.version1_nodrafts))

    def test_version_missing(self):
        """
        Check that get_version returns None if no version number is specified,
        and the archive is not version 0.
        """
        self.assertIsNone(self._version_test(self.no_version))

    def _version_test(self, archive_dir):
        """
        Helper function for version tests.
        """
        root = os.listdir(archive_dir)
        course_directory = archive_dir / root[0]
        return get_version(course_directory)

    def _verify_conversion(self, source_archive, comparison_archive):
        """
        Helper function for conversion tests.
        """
        convert_between_versions(source_archive, self.result_dir)
        self.assertTrue(directories_equal(self.result_dir, comparison_archive))
