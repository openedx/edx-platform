"""
Unittests for migrating a course to split mongo
"""
import unittest

from django.core.management import CommandError, call_command
from contentstore.management.commands.migrate_to_split import Command
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


class TestArgParsing(unittest.TestCase):
    """
    Tests for parsing arguments for the `migrate_to_split` management command
    """
    def setUp(self):
        super(TestArgParsing, self).setUp()
        self.command = Command()

    def test_no_args(self):
        """
        Test the arg length error
        """
        errstring = "migrate_to_split requires at least two arguments"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()

    def test_invalid_location(self):
        """
        Test passing an unparsable course id
        """
        errstring = "Invalid location string"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("foo", "bar")

    def test_nonexistent_user_id(self):
        """
        Test error for using an unknown user primary key
        """
        errstring = "No user found identified by 99"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("org/course/name", "99")

    def test_nonexistent_user_email(self):
        """
        Test error for using an unknown user email
        """
        errstring = "No user found identified by fake@example.com"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("org/course/name", "fake@example.com")


# pylint: disable=no-member, protected-access
class TestMigrateToSplit(ModuleStoreTestCase):
    """
    Unit tests for migrating a course from old mongo to split mongo
    """

    def setUp(self):
        super(TestMigrateToSplit, self).setUp()
        self.course = CourseFactory(default_store=ModuleStoreEnum.Type.mongo)

    def test_user_email(self):
        """
        Test migration for real as well as testing using an email addr to id the user
        """
        call_command(
            "migrate_to_split",
            str(self.course.id),
            str(self.user.email),
        )
        split_store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)
        new_key = split_store.make_course_key(self.course.id.org, self.course.id.course, self.course.id.run)
        self.assertTrue(
            split_store.has_course(new_key),
            "Could not find course"
        )
        # I put this in but realized that the migrator doesn't make the new course the
        # default mapping in mixed modulestore. I left the test here so we can debate what it ought to do.
#         self.assertEqual(
#             ModuleStoreEnum.Type.split,
#             modulestore()._get_modulestore_for_courselike(new_key).get_modulestore_type(),
#             "Split is not the new default for the course"
#         )

    def test_user_id(self):
        """
        Test that the command accepts the user's primary key
        """
        # lack of error implies success
        call_command(
            "migrate_to_split",
            str(self.course.id),
            str(self.user.id),
        )

    def test_locator_string(self):
        """
        Test importing to a different course id
        """
        call_command(
            "migrate_to_split",
            str(self.course.id),
            str(self.user.id),
            "org.dept", "name", "run",
        )
        split_store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)
        locator = split_store.make_course_key("org.dept", "name", "run")
        course_from_split = split_store.get_course(locator)
        self.assertIsNotNone(course_from_split)

        # Getting the original course with mongo course_id
        mongo_store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)
        mongo_locator = mongo_store.make_course_key(self.course.id.org, self.course.id.course, self.course.id.run)
        course_from_mongo = mongo_store.get_course(mongo_locator)
        self.assertIsNotNone(course_from_mongo)

        # Throws ItemNotFoundError when try to access original course with split course_id
        split_locator = split_store.make_course_key(self.course.id.org, self.course.id.course, self.course.id.run)
        with self.assertRaises(ItemNotFoundError):
            mongo_store.get_course(split_locator)
