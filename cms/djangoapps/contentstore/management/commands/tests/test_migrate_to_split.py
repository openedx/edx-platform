"""
Unittests for migrating a course to split mongo
"""
import unittest

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from contentstore.management.commands.migrate_to_split import Command
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from opaque_keys.edx.locator import CourseLocator
# pylint: disable=E1101


@unittest.skip("Not fixing split mongo until we land this long branch")
class TestArgParsing(unittest.TestCase):
    """
    Tests for parsing arguments for the `migrate_to_split` management command
    """
    def setUp(self):
        self.command = Command()

    def test_no_args(self):
        errstring = "migrate_to_split requires at least two arguments"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle()

    def test_invalid_location(self):
        errstring = "Invalid location string"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("foo", "bar")

    def test_nonexistant_user_id(self):
        errstring = "No user found identified by 99"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("i4x://org/course/category/name", "99")

    def test_nonexistant_user_email(self):
        errstring = "No user found identified by fake@example.com"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("i4x://org/course/category/name", "fake@example.com")


@unittest.skip("Not fixing split mongo until we land this long branch")
class TestMigrateToSplit(ModuleStoreTestCase):
    """
    Unit tests for migrating a course from old mongo to split mongo
    """

    def setUp(self):
        super(TestMigrateToSplit, self).setUp()
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'
        self.user = User.objects.create_user(uname, email, password)
        self.course = CourseFactory()
        self.addCleanup(ModuleStoreTestCase.drop_mongo_collections)
        self.addCleanup(clear_existing_modulestores)

    def test_user_email(self):
        call_command(
            "migrate_to_split",
            str(self.course.location),
            str(self.user.email),
        )
        course_from_split = modulestore('split').get_course(self.course.id)
        self.assertIsNotNone(course_from_split)

    def test_user_id(self):
        call_command(
            "migrate_to_split",
            str(self.course.location),
            str(self.user.id),
        )
        course_from_split = modulestore('split').get_course(self.course.id)
        self.assertIsNotNone(course_from_split)

    def test_locator_string(self):
        call_command(
            "migrate_to_split",
            str(self.course.location),
            str(self.user.id),
            "org.dept+name.run",
        )
        locator = CourseLocator(org="org.dept", course="name", run="run", branch=ModuleStoreEnum.RevisionOption.published_only)
        course_from_split = modulestore('split').get_course(locator)
        self.assertIsNotNone(course_from_split)
