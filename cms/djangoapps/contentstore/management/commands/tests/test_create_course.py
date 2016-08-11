"""
Unittests for creating a course in an chosen modulestore
"""
import unittest
import ddt
from django.core.management import CommandError, call_command

from contentstore.management.commands.create_course import Command
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore


class TestArgParsing(unittest.TestCase):
    """
    Tests for parsing arguments for the `create_course` management command
    """
    def setUp(self):
        super(TestArgParsing, self).setUp()

        self.command = Command()

    def test_no_args(self):
        errstring = "create_course requires 5 arguments"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle('create_course')

    def test_invalid_store(self):
        with self.assertRaises(CommandError):
            self.command.handle("foo", "user@foo.org", "org", "course", "run")

    def test_nonexistent_user_id(self):
        errstring = "No user 99 found"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("split", "99", "org", "course", "run")

    def test_nonexistent_user_email(self):
        errstring = "No user fake@example.com found"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("mongo", "fake@example.com", "org", "course", "run")


@ddt.ddt
class TestCreateCourse(ModuleStoreTestCase):
    """
    Unit tests for creating a course in either old mongo or split mongo via command line
    """

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_all_stores_user_email(self, store):
        call_command(
            "create_course",
            store,
            str(self.user.email),
            "org", "course", "run"
        )
        new_key = modulestore().make_course_key("org", "course", "run")
        self.assertTrue(
            modulestore().has_course(new_key),
            "Could not find course in {}".format(store)
        )
        # pylint: disable=protected-access
        self.assertEqual(store, modulestore()._get_modulestore_for_courselike(new_key).get_modulestore_type())

    @ddt.data(ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.mongo)
    def test_get_course_with_different_case(self, default_store):
        """
        Tests that course can not be accessed with different case.

        Scenario:
            Create a course with lower case keys inside `bulk_operations` with `ignore_case=True`.
            Verify that course is created.
            Verify that get course from store using same course id but different case is not accessible.
        """
        org = 'org1'
        number = 'course1'
        run = 'run1'
        with self.store.default_store(default_store):
            lowercase_course_id = self.store.make_course_key(org, number, run)
            with self.store.bulk_operations(lowercase_course_id, ignore_case=True):
                # Create course with lowercase key & Verify that store returns course.
                self.store.create_course(
                    lowercase_course_id.org,
                    lowercase_course_id.course,
                    lowercase_course_id.run,
                    self.user.id
                )
                course = self.store.get_course(lowercase_course_id)
                self.assertIsNotNone(course, 'Course not found using lowercase course key.')
                self.assertEqual(unicode(course.id), unicode(lowercase_course_id))

                # Verify store does not return course with different case.
                uppercase_course_id = self.store.make_course_key(org.upper(), number.upper(), run.upper())
                course = self.store.get_course(uppercase_course_id)
                self.assertIsNone(course, 'Course should not be accessed with uppercase course id.')
