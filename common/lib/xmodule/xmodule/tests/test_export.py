# -*- coding: utf-8 -*-
"""
Tests of XML export
"""


import shutil
import unittest
from datetime import datetime, timedelta, tzinfo
from tempfile import mkdtemp
from textwrap import dedent

import ddt
import lxml.etree
import mock
import pytz
import six
from django.utils.translation import ugettext_lazy
from fs.osfs import OSFS
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from path import Path as path
from six import text_type
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String
from xblock.test.tools import blocks_are_equivalent

from xmodule.modulestore import EdxJSONEncoder
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.tests import DATA_DIR
from xmodule.x_module import XModuleMixin


def strip_filenames(descriptor):
    """
    Recursively strips 'filename' from all children's definitions.
    """
    print("strip filename from {desc}".format(desc=text_type(descriptor.location)))
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

    @mock.patch('xmodule.video_module.video_module.edxval_api', None)
    @mock.patch('xmodule.course_module.requests.get')
    @ddt.data(
        u"toy",
        u"simple",
        u"conditional_and_poll",
        u"conditional",
        u"self_assessment",
        u"test_exam_registration",
        u"word_cloud",
        u"pure_xblock",
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
        print("Copying test course to temp dir {0}".format(root_dir))

        data_dir = path(DATA_DIR)
        shutil.copytree(data_dir / course_dir, root_dir / course_dir)

        print("Starting import")
        initial_import = XMLModuleStore(root_dir, source_dirs=[course_dir], xblock_mixins=(XModuleMixin,))

        courses = initial_import.get_courses()
        self.assertEqual(len(courses), 1)
        initial_course = courses[0]

        # export to the same directory--that way things like the custom_tags/ folder
        # will still be there.
        print("Starting export")
        file_system = OSFS(root_dir)
        initial_course.runtime.export_fs = file_system.makedir(course_dir, recreate=True)
        root = lxml.etree.Element('root')

        initial_course.add_xml_to_node(root)
        with initial_course.runtime.export_fs.open('course.xml', 'wb') as course_xml:
            lxml.etree.ElementTree(root).write(course_xml, encoding='utf-8')

        print("Starting second import")
        second_import = XMLModuleStore(root_dir, source_dirs=[course_dir], xblock_mixins=(XModuleMixin,))

        courses2 = second_import.get_courses()
        self.assertEqual(len(courses2), 1)
        exported_course = courses2[0]

        print("Checking course equality")

        # HACK: filenames change when changing file formats
        # during imports from old-style courses.  Ignore them.
        strip_filenames(initial_course)
        strip_filenames(exported_course)

        self.assertTrue(blocks_are_equivalent(initial_course, exported_course))
        self.assertEqual(initial_course.id, exported_course.id)
        course_id = initial_course.id

        print("Checking key equality")
        six.assertCountEqual(
            self,
            list(initial_import.modules[course_id].keys()),
            list(second_import.modules[course_id].keys())
        )

        print("Checking module equality")
        for location in initial_import.modules[course_id].keys():
            print(("Checking", location))
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
        loc = BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'category', 'name')
        self.assertEqual(text_type(loc), self.encoder.default(loc))

        loc = BlockUsageLocator(CourseLocator('org', 'course', 'run', branch='version'), 'category', 'name')
        self.assertEqual(text_type(loc), self.encoder.default(loc))

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

    def test_encode_unicode_lazy_text(self):
        """
        Verify that the encoding is functioning fine with lazy text
        """

        # Initializing a lazy text object with Unicode
        unicode_text = u"Your 𝓟𝓵𝓪𝓽𝓯𝓸𝓻𝓶 Name Here"
        lazy_text = ugettext_lazy(unicode_text)

        self.assertEqual(
            unicode_text,
            self.encoder.default(lazy_text)
        )
