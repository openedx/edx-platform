"""
Unittests for migrating a course to split mongo
"""
import unittest

from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.test.utils import override_settings
from contentstore.management.commands.migrate_to_split import Command
from contentstore.tests.modulestore_config import TEST_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.django import loc_mapper


class TestArgParsing(unittest.TestCase):
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


@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestMigrateToSplit(ModuleStoreTestCase):
    """
    Unit tests for importing a course from command line
    """

    def setUp(self):
        super(TestMigrateToSplit, self).setUp()
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'
        self.user = User.objects.create_user(uname, email, password)
        self.course = CourseFactory()

    def test_happy_path_email(self):
        call_command(
            "migrate_to_split",
            str(self.course.location),
            str(self.user.email),
        )
        locator = loc_mapper().translate_location(self.course.id, self.course.location)
        course_from_split = modulestore('split').get_course(locator)
        self.assertIsNotNone(course_from_split)

    def test_happy_path_user_id(self):
        call_command(
            "migrate_to_split",
            str(self.course.location),
            str(self.user.id),
        )
        locator = loc_mapper().translate_location(self.course.id, self.course.location)
        course_from_split = modulestore('split').get_course(locator)
        self.assertIsNotNone(course_from_split)
