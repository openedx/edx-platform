"""
Unittests for deleting a split mongo course
"""
import unittest
from StringIO import StringIO
from mock import patch

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from contentstore.management.commands.rollback_split_course import Command
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.persistent_factories import PersistentCourseFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore, loc_mapper
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.split_migrator import SplitMigrator
from xmodule.modulestore import ModuleStoreEnum
# pylint: disable=E1101
# pylint: disable=W0212


@unittest.skip("Not fixing split mongo until we land opaque-keys 0.9")
class TestArgParsing(unittest.TestCase):
    """
    Tests for parsing arguments for the `rollback_split_course` management command
    """
    def setUp(self):
        self.command = Command()

    def test_no_args(self):
        errstring = "rollback_split_course requires at least one argument"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()

    def test_invalid_locator(self):
        errstring = "Invalid locator string !?!"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("!?!")


@unittest.skip("Not fixing split mongo until we land opaque-keys 0.9")
class TestRollbackSplitCourseNoOldMongo(ModuleStoreTestCase):
    """
    Unit tests for rolling back a split-mongo course from command line,
    where the course doesn't exist in the old mongo store
    """

    def setUp(self):
        super(TestRollbackSplitCourseNoOldMongo, self).setUp()
        self.course = PersistentCourseFactory()

    def test_no_old_course(self):
        locator = self.course.location
        errstring = "course does not exist in the old Mongo store"
        with self.assertRaisesRegexp(CommandError, errstring):
            Command().handle(str(locator))


@unittest.skip("Not fixing split mongo until we land opaque-keys 0.9")
class TestRollbackSplitCourseNoSplitMongo(ModuleStoreTestCase):
    """
    Unit tests for rolling back a split-mongo course from command line,
    where the course doesn't exist in the split mongo store
    """

    def setUp(self):
        super(TestRollbackSplitCourseNoSplitMongo, self).setUp()
        self.old_course = CourseFactory()

    def test_nonexistent_locator(self):
        locator = loc_mapper().translate_location(self.old_course.location)
        errstring = "No course found with locator"
        with self.assertRaisesRegexp(CommandError, errstring):
            Command().handle(str(locator))


@unittest.skip("Not fixing split mongo until we land opaque-keys 0.9")
class TestRollbackSplitCourse(ModuleStoreTestCase):
    """
    Unit tests for rolling back a split-mongo course from command line
    """
    def setUp(self):
        super(TestRollbackSplitCourse, self).setUp()
        self.old_course = CourseFactory()
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'
        self.user = User.objects.create_user(uname, email, password)

        # migrate old course to split
        migrator = SplitMigrator(
            draft_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo),
            split_modulestore=modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split),
            loc_mapper=loc_mapper(),
        )
        migrator.migrate_mongo_course(self.old_course.location, self.user)
        self.course = modulestore('split').get_course(self.old_course.id)

    @patch("sys.stdout", new_callable=StringIO)
    def test_happy_path(self, mock_stdout):
        course_id = self.course.id
        call_command(
            "rollback_split_course",
            str(course_id),
        )
        with self.assertRaises(ItemNotFoundError):
            modulestore('split').get_course(course_id)

        self.assertIn("Course rolled back successfully", mock_stdout.getvalue())

