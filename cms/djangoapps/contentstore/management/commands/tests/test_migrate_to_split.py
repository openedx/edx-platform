"""
Unittests for migrating a course to split mongo
"""


import six
from django.core.management import CommandError, call_command
from django.test import TestCase

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestArgParsing(TestCase):
    """
    Tests for parsing arguments for the `migrate_to_split` management command
    """
    def setUp(self):
        super(TestArgParsing, self).setUp()

    def test_no_args(self):
        """
        Test the arg length error
        """
        if six.PY2:
            errstring = "Error: too few arguments"
        else:
            errstring = "Error: the following arguments are required: course_key, email"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command("migrate_to_split")

    def test_invalid_location(self):
        """
        Test passing an unparsable course id
        """
        errstring = "Invalid location string"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command("migrate_to_split", "foo", "bar")

    def test_nonexistent_user_id(self):
        """
        Test error for using an unknown user primary key
        """
        errstring = "No user found identified by 99"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command("migrate_to_split", "org/course/name", "99")

    def test_nonexistent_user_email(self):
        """
        Test error for using an unknown user email
        """
        errstring = "No user found identified by fake@example.com"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command("migrate_to_split", "org/course/name", "fake@example.com")


# pylint: disable=protected-access
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
            org="org.dept",
            course="name",
            run="run",
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
