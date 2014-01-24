"""Tests for Django management commands"""

import json
import shutil
from StringIO import StringIO
import tarfile
from tempfile import mkdtemp

from path import path

from django.core.management import call_command
from django.test.utils import override_settings
from django.test.testcases import TestCase

from courseware.tests.modulestore_config import TEST_DATA_XML_MODULESTORE
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.xml_importer import import_from_xml

DATA_DIR = 'common/test/data/'

TEST_COURSE_ID = 'edX/simple/2012_Fall'


class CommandsTestBase(TestCase):
    """
    Base class for testing different django commands.

    Must be subclassed using override_settings set to the modulestore
    to be tested.

    """

    def setUp(self):
        self.loaded_courses = self.load_courses()

    def load_courses(self):
        """Load test courses and return list of ids"""
        store = modulestore()

        courses = store.get_courses()
        if TEST_COURSE_ID not in [c.id for c in courses]:
            import_from_xml(store, DATA_DIR, ['toy', 'simple'])

        return [course.id for course in store.get_courses()]

    def call_command(self, name, *args, **kwargs):
        """Call management command and return output"""
        out = StringIO()  # To Capture the output of the command
        call_command(name, *args, stdout=out, **kwargs)
        out.seek(0)
        return out.read()

    def test_dump_course_ids(self):
        kwargs = {'modulestore': 'default'}
        output = self.call_command('dump_course_ids', **kwargs)
        dumped_courses = output.strip().split('\n')
        self.assertEqual(self.loaded_courses, dumped_courses)

    def test_dump_course_structure(self):
        args = [TEST_COURSE_ID]
        kwargs = {'modulestore': 'default'}
        output = self.call_command('dump_course_structure', *args, **kwargs)

        dump = json.loads(output)

        # check that all elements in the course structure have metadata,
        # but not inherited metadata:
        for element_name in dump:
            element = dump[element_name]
            self.assertIn('metadata', element)
            self.assertIn('children', element)
            self.assertIn('category', element)
            self.assertNotIn('inherited_metadata', element)

        # Check a few elements in the course dump

        parent_id = 'i4x://edX/simple/chapter/Overview'
        self.assertEqual(dump[parent_id]['category'], 'chapter')
        self.assertEqual(len(dump[parent_id]['children']), 3)

        child_id = dump[parent_id]['children'][1]
        self.assertEqual(dump[child_id]['category'], 'videosequence')
        self.assertEqual(len(dump[child_id]['children']), 2)

        video_id = 'i4x://edX/simple/video/Welcome'
        self.assertEqual(dump[video_id]['category'], 'video')
        self.assertEqual(len(dump[video_id]['metadata']), 4)
        self.assertIn('youtube_id_1_0', dump[video_id]['metadata'])

        # Check if there are the right number of elements

        self.assertEqual(len(dump), 16)

    def test_dump_inherited_course_structure(self):
        args = [TEST_COURSE_ID]
        kwargs = {'modulestore': 'default', 'inherited': True}
        output = self.call_command('dump_course_structure', *args, **kwargs)
        dump = json.loads(output)
        # check that all elements in the course structure have inherited metadata,
        # and that it contains a particular value as well:
        for element_name in dump:
            element = dump[element_name]
            self.assertIn('metadata', element)
            self.assertIn('children', element)
            self.assertIn('category', element)
            self.assertIn('inherited_metadata', element)
            self.assertIsNone(element['inherited_metadata']['ispublic'])
            # ... but does not contain inherited metadata containing a default value:
            self.assertNotIn('due', element['inherited_metadata'])

    def test_dump_inherited_course_structure_with_defaults(self):
        args = [TEST_COURSE_ID]
        kwargs = {'modulestore': 'default', 'inherited': True, 'inherited_defaults': True}
        output = self.call_command('dump_course_structure', *args, **kwargs)
        dump = json.loads(output)
        # check that all elements in the course structure have inherited metadata,
        # and that it contains a particular value as well:
        for element_name in dump:
            element = dump[element_name]
            self.assertIn('metadata', element)
            self.assertIn('children', element)
            self.assertIn('category', element)
            self.assertIn('inherited_metadata', element)
            self.assertIsNone(element['inherited_metadata']['ispublic'])
            # ... and contains inherited metadata containing a default value:
            self.assertIsNone(element['inherited_metadata']['due'])

    def test_export_course(self):
        tmp_dir = path(mkdtemp())
        filename = tmp_dir / 'test.tar.gz'
        try:
            self.run_export_course(filename)
            with tarfile.open(filename) as tar_file:
                self.check_export_file(tar_file)

        finally:
            shutil.rmtree(tmp_dir)

    def test_export_course_stdout(self):
        output = self.run_export_course('-')
        with tarfile.open(fileobj=StringIO(output)) as tar_file:
            self.check_export_file(tar_file)

    def run_export_course(self, filename):  # pylint: disable=missing-docstring
        args = ['edX/simple/2012_Fall', filename]
        kwargs = {'modulestore': 'default'}
        return self.call_command('export_course', *args, **kwargs)

    def check_export_file(self, tar_file):  # pylint: disable=missing-docstring
        names = tar_file.getnames()

        # Check if some of the files are present.

        # The rest is of the code should be covered by the tests for
        # xmodule.modulestore.xml_exporter, used by the dump_course command

        assert_in = self.assertIn
        assert_in('edX-simple-2012_Fall', names)
        assert_in('edX-simple-2012_Fall/policies/2012_Fall/policy.json', names)
        assert_in('edX-simple-2012_Fall/html/toylab.html', names)
        assert_in('edX-simple-2012_Fall/videosequence/A_simple_sequence.xml', names)
        assert_in('edX-simple-2012_Fall/sequential/Lecture_2.xml', names)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class CommandsXMLTestCase(CommandsTestBase, ModuleStoreTestCase):
    """
    Test case for management commands using the xml modulestore.

    """


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class CommandsMongoTestCase(CommandsTestBase, ModuleStoreTestCase):
    """
    Test case for management commands using the mongo modulestore.

    """


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CommandsMixedTestCase(CommandsTestBase, ModuleStoreTestCase):
    """
    Test case for management commands. Using the mixed modulestore.

    """
