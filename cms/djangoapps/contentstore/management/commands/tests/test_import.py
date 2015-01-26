"""
Unittests for importing a course via management command
"""

import os
from path import path
import shutil
import tempfile

from django.core.management import call_command

from django_comment_common.utils import are_permissions_roles_seeded
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TestImport(ModuleStoreTestCase):
    """
    Unit tests for importing a course from command line
    """

    def create_course_xml(self, content_dir, course_id):
        directory = tempfile.mkdtemp(dir=content_dir)
        os.makedirs(os.path.join(directory, "course"))
        with open(os.path.join(directory, "course.xml"), "w+") as f:
            f.write('<course url_name="{0.run}" org="{0.org}" '
                    'course="{0.course}"/>'.format(course_id))

        with open(os.path.join(directory, "course", "{0.run}.xml".format(course_id)), "w+") as f:
            f.write('<course></course>')

        return directory

    def setUp(self):
        """
        Build course XML for importing
        """
        super(TestImport, self).setUp()
        self.content_dir = path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.content_dir)

        self.base_course_key = self.store.make_course_key(u'edX', u'test_import_course', u'2013_Spring')
        self.truncated_key = self.store.make_course_key(u'edX', u'test_import', u'2014_Spring')

        # Create good course xml
        self.good_dir = self.create_course_xml(self.content_dir, self.base_course_key)

        # Create course XML where TRUNCATED_COURSE.org == BASE_COURSE_ID.org
        # and BASE_COURSE_ID.startswith(TRUNCATED_COURSE.course)
        self.course_dir = self.create_course_xml(self.content_dir, self.truncated_key)

    def test_forum_seed(self):
        """
        Tests that forum roles were created with import.
        """
        self.assertFalse(are_permissions_roles_seeded(self.base_course_key))
        call_command('import', self.content_dir, self.good_dir)
        self.assertTrue(are_permissions_roles_seeded(self.base_course_key))

    def test_truncated_course_with_url(self):
        """
        Check to make sure an import only blocks true duplicates: new
        courses with similar but not unique org/course combinations aren't
        blocked if the original course's course starts with the new course's
        org/course combinations (i.e. EDx/0.00x/Spring -> EDx/0.00/Spring)
        """
        # Load up base course and verify it is available
        call_command('import', self.content_dir, self.good_dir)
        store = modulestore()
        self.assertIsNotNone(store.get_course(self.base_course_key))

        # Now load up the course with a similar course_id and verify it loads
        call_command('import', self.content_dir, self.course_dir)
        self.assertIsNotNone(store.get_course(self.truncated_key))
