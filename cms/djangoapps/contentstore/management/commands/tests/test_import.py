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
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.locations import SlashSeparatedCourseKey


@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestImport(ModuleStoreTestCase):
    """
    Unit tests for importing a course from command line
    """

    COURSE_USAGE_KEY = SlashSeparatedCourseKey(u'edX', u'test_import_course', u'2013_Spring')

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
            f.write('<course url_name="2013_Spring" org="edX" course="test_import_course"/>')

        with open(os.path.join(self.good_dir, "course", "2013_Spring.xml"), "w+") as f:
            f.write('<course></course>')

    def test_forum_seed(self):
        """
        Tests that forum roles were created with import.
        """
        self.assertFalse(are_permissions_roles_seeded(self.COURSE_USAGE_KEY))
        call_command('import', self.content_dir, self.good_dir)
        self.assertTrue(are_permissions_roles_seeded(self.COURSE_USAGE_KEY))
