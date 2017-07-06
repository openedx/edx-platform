# coding=utf-8

"""Tests for Django management commands"""

import json
from nose.plugins.attrib import attr
from path import Path as path
import shutil
from StringIO import StringIO
import tarfile
from tempfile import mkdtemp
import factory

from django.conf import settings
from django.core.management import call_command

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MONGO_MODULESTORE, TEST_DATA_SPLIT_MODULESTORE
)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.xml_importer import import_course_from_xml

DATA_DIR = settings.COMMON_TEST_DATA_ROOT
XML_COURSE_DIRS = ['simple']


@attr('shard_1')
class CommandsTestBase(SharedModuleStoreTestCase):
    """
    Base class for testing different django commands.

    Must be subclassed using override_settings set to the modulestore
    to be tested.

    """
    __test__ = False
    url_name = '2012_Fall'

    @classmethod
    def setUpClass(cls):
        super(CommandsTestBase, cls).setUpClass()
        cls.test_course_key = modulestore().make_course_key("edX", "simple", "2012_Fall")
        cls.loaded_courses = cls.load_courses()

    @classmethod
    def load_courses(cls):
        """Load test courses and return list of ids"""
        store = modulestore()

        unique_org = factory.Sequence(lambda n: 'edX.%d' % n)
        cls.course = CourseFactory.create(
            emit_signals=True,
            org=unique_org,
            course='simple',
            run="run",
            display_name=u'2012_Fáĺĺ',
            modulestore=store
        )

        cls.discussion = ItemFactory.create(
            category='discussion', parent_location=cls.course.location
        )

        courses = store.get_courses()
        # NOTE: if xml store owns these, it won't import them into mongo
        if cls.test_course_key not in [c.id for c in courses]:
            import_course_from_xml(
                store, ModuleStoreEnum.UserID.mgmt_command, DATA_DIR, XML_COURSE_DIRS, create_if_not_present=True
            )

        return [course.id for course in store.get_courses()]

    def call_command(self, name, *args, **kwargs):
        """Call management command and return output"""
        out = StringIO()  # To Capture the output of the command
        call_command(name, *args, stdout=out, **kwargs)
        out.seek(0)
        return out.read()

    def test_dump_course_ids(self):
        output = self.call_command('dump_course_ids')
        dumped_courses = output.decode('utf-8').strip().split('\n')
        course_ids = {unicode(course_id) for course_id in self.loaded_courses}
        dumped_ids = set(dumped_courses)
        self.assertEqual(course_ids, dumped_ids)

    def test_correct_course_structure_metadata(self):
        course_id = unicode(self.test_course_key)
        args = [course_id]
        kwargs = {'modulestore': 'default'}

        try:
            output = self.call_command('dump_course_structure', *args, **kwargs)
        except TypeError, exception:
            self.fail(exception)

        dump = json.loads(output)
        self.assertGreater(len(dump.values()), 0)

    def test_dump_course_structure(self):
        args = [unicode(self.test_course_key)]
        kwargs = {'modulestore': 'default'}
        output = self.call_command('dump_course_structure', *args, **kwargs)

        dump = json.loads(output)

        # check that all elements in the course structure have metadata,
        # but not inherited metadata:
        for element in dump.itervalues():
            self.assertIn('metadata', element)
            self.assertIn('children', element)
            self.assertIn('category', element)
            self.assertNotIn('inherited_metadata', element)

        # Check a few elements in the course dump
        test_course_key = self.test_course_key
        parent_id = unicode(test_course_key.make_usage_key('chapter', 'Overview'))
        self.assertEqual(dump[parent_id]['category'], 'chapter')
        self.assertEqual(len(dump[parent_id]['children']), 3)

        child_id = dump[parent_id]['children'][1]
        self.assertEqual(dump[child_id]['category'], 'videosequence')
        self.assertEqual(len(dump[child_id]['children']), 2)

        video_id = unicode(test_course_key.make_usage_key('video', 'Welcome'))
        self.assertEqual(dump[video_id]['category'], 'video')
        self.assertItemsEqual(
            dump[video_id]['metadata'].keys(),
            ['download_video', 'youtube_id_0_75', 'youtube_id_1_0', 'youtube_id_1_25', 'youtube_id_1_5']
        )
        self.assertIn('youtube_id_1_0', dump[video_id]['metadata'])

        # Check if there are the right number of elements

        self.assertEqual(len(dump), 17)

    def test_dump_inherited_course_structure(self):
        args = [unicode(self.test_course_key)]
        kwargs = {'modulestore': 'default', 'inherited': True}
        output = self.call_command('dump_course_structure', *args, **kwargs)
        dump = json.loads(output)
        # check that all elements in the course structure have inherited metadata,
        # and that it contains a particular value as well:
        for element in dump.itervalues():
            self.assertIn('metadata', element)
            self.assertIn('children', element)
            self.assertIn('category', element)
            self.assertIn('inherited_metadata', element)
            # ... but does not contain inherited metadata containing a default value:
            self.assertNotIn('due', element['inherited_metadata'])

    def test_dump_inherited_course_structure_with_defaults(self):
        args = [unicode(self.test_course_key)]
        kwargs = {'modulestore': 'default', 'inherited': True, 'inherited_defaults': True}
        output = self.call_command('dump_course_structure', *args, **kwargs)
        dump = json.loads(output)
        # check that all elements in the course structure have inherited metadata,
        # and that it contains a particular value as well:
        for element in dump.itervalues():
            self.assertIn('metadata', element)
            self.assertIn('children', element)
            self.assertIn('category', element)
            self.assertIn('inherited_metadata', element)
            # ... and contains inherited metadata containing a default value:
            self.assertIsNone(element['inherited_metadata']['due'])

    def test_export_discussion_ids(self):
        output = self.call_command('dump_course_structure', unicode(self.course.id))
        dump = json.loads(output)
        dumped_id = dump[unicode(self.discussion.location)]['metadata']['discussion_id']
        self.assertEqual(dumped_id, self.discussion.discussion_id)

    def test_export_discussion_id_custom_id(self):
        output = self.call_command('dump_course_structure', unicode(self.test_course_key))
        dump = json.loads(output)
        discussion_key = unicode(self.test_course_key.make_usage_key('discussion', 'custom_id'))
        dumped_id = dump[unicode(discussion_key)]['metadata']['discussion_id']
        self.assertEqual(dumped_id, "custom")

    def test_export_course(self):
        tmp_dir = path(mkdtemp())
        self.addCleanup(shutil.rmtree, tmp_dir)
        filename = tmp_dir / 'test.tar.gz'

        self.run_export_course(filename)
        with tarfile.open(filename) as tar_file:
            self.check_export_file(tar_file)

    def test_export_course_stdout(self):
        output = self.run_export_course('-')
        with tarfile.open(fileobj=StringIO(output)) as tar_file:
            self.check_export_file(tar_file)

    def run_export_course(self, filename):  # pylint: disable=missing-docstring
        args = [unicode(self.test_course_key), filename]
        kwargs = {'modulestore': 'default'}
        return self.call_command('export_course', *args, **kwargs)

    def check_export_file(self, tar_file):  # pylint: disable=missing-docstring
        names = tar_file.getnames()

        # Check if some of the files are present.

        # The rest is of the code should be covered by the tests for
        # xmodule.modulestore.xml_exporter, used by the dump_course command

        assert_in = self.assertIn
        assert_in('edX-simple-2012_Fall', names)
        assert_in('edX-simple-2012_Fall/policies/{}/policy.json'.format(self.url_name), names)
        assert_in('edX-simple-2012_Fall/html/toylab.html', names)
        assert_in('edX-simple-2012_Fall/videosequence/A_simple_sequence.xml', names)
        assert_in('edX-simple-2012_Fall/sequential/Lecture_2.xml', names)


class CommandsMongoTestCase(CommandsTestBase):
    """
    Test case for management commands using the mixed mongo modulestore with old mongo as the default.

    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE
    __test__ = True


class CommandSplitMongoTestCase(CommandsTestBase):
    """
    Test case for management commands using the mixed mongo modulestore with split as the default.

    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE
    __test__ = True
    url_name = 'course'
