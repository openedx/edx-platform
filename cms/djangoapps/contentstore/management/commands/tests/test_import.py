"""
Unittests for importing a course via management command
"""

import os
from path import path
import shutil
import tempfile

from django.core.management import call_command
from django.test.utils import override_settings

from contentstore.tests.modulestore_config import TEST_MODULESTORE
from django_comment_common.utils import are_permissions_roles_seeded
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.locations import SlashSeparatedCourseKey


@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestImport(ModuleStoreTestCase):
    """
    Unit tests for importing a course from command line
    """

    COURSE_KEY = SlashSeparatedCourseKey(u'edX', u'test_import_course', u'2013_Spring')
    DIFF_KEY = SlashSeparatedCourseKey(u'edX', u'test_import_course', u'2014_Spring')

    def setUp(self):
        """
        Build course XML for importing
        """
        super(TestImport, self).setUp()
        self.content_dir = path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.content_dir)

        # Create good course xml
        self.good_dir = tempfile.mkdtemp(dir=self.content_dir)
        os.makedirs(os.path.join(self.good_dir, "course"))
        with open(os.path.join(self.good_dir, "course.xml"), "w+") as f:
            f.write('<course url_name="{0.run}" org="{0.org}" '
                    'course="{0.course}"/>'.format(self.COURSE_KEY))

        with open(os.path.join(self.good_dir, "course", "{0.run}.xml".format(self.COURSE_KEY)), "w+") as f:
            f.write('<course></course>')

        # Create run changed course xml
        self.dupe_dir = tempfile.mkdtemp(dir=self.content_dir)
        os.makedirs(os.path.join(self.dupe_dir, "course"))
        with open(os.path.join(self.dupe_dir, "course.xml"), "w+") as f:
            f.write('<course url_name="{0.run}" org="{0.org}" '
                    'course="{0.course}"/>'.format(self.DIFF_KEY))

        with open(os.path.join(self.dupe_dir, "course", "{0.run}.xml".format(self.DIFF_KEY)), "w+") as f:
            f.write('<course></course>')

    def test_forum_seed(self):
        """
        Tests that forum roles were created with import.
        """
        self.assertFalse(are_permissions_roles_seeded(self.COURSE_KEY))
        call_command('import', self.content_dir, self.good_dir)
        self.assertTrue(are_permissions_roles_seeded(self.COURSE_KEY))

    def test_duplicate_with_url(self):
        """
        Check to make sure an import doesn't import courses that have the
        same org and course, but they have different runs in order to
        prevent modulestore "findone" exceptions on deletion
        """
        # Load up base course and verify it is available
        call_command('import', self.content_dir, self.good_dir)
        store = modulestore()
        self.assertIsNotNone(store.get_course(self.COURSE_KEY))

        # Now load up duped course and verify it doesn't load
        call_command('import', self.content_dir, self.dupe_dir)
        self.assertIsNone(store.get_course(self.DIFF_KEY))
        self.assertTrue(are_permissions_roles_seeded(self.COURSE_KEY))
