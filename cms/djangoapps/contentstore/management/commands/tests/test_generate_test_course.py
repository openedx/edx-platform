"""
Unittest for generate a test course in an given modulestore
"""
import unittest
import ddt
from django.core.management import CommandError, call_command

from contentstore.management.commands.generate_test_course import Command
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.django import modulestore


@ddt.ddt
class TestGenerateTestCourse(ModuleStoreTestCase):
    """
    Unit tests for creating a course in either old mongo or split mongo via command line
    """

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_generate_course_in_stores(self, store):
        """
        Test that courses are created successfully for both ModuleStores
        """
        arg = (
            '{"store":"' + store + '",' +
            '"user":"' + self.user.email + '",' +
            '"organization":"test-course-generator",' +
            '"number":"1",' +
            '"run":"1",' +
            '"fields":{"display_name":"test-course"}}'
        )
        call_command("generate_test_course", arg)
        key = modulestore().make_course_key("test-course-generator", "1", "1")
        self.assertTrue(modulestore().has_course(key))

    def test_invalid_json(self):
        """
        Test that providing an invalid JSON object will result in the appropriate command error
        """
        error_msg = "Invalid JSON"
        with self.assertRaisesRegexp(CommandError, error_msg):
            arg = "invalid_json"
            call_command("generate_test_course", arg)

    def test_missing_fields(self):
        """
        Test that missing required fields in JSON object will result in the appropriate command error
        """
        error_msg = "JSON object is missing required fields"
        with self.assertRaisesRegexp(CommandError, error_msg):
            arg = (
                '{"store":"invalid_store",' +
                '"user":"user@example.com",' +
                '"organization":"test-course-generator"}'
            )
            call_command("generate_test_course", arg)

    def test_invalid_store(self):
        """
        Test that providing an invalid store option will result in the appropriate command error
        """
        error_msg = "Modulestore invalid_store is not valid"
        with self.assertRaisesRegexp(CommandError, error_msg):
            arg = (
                '{"store":"invalid_store",' +
                '"user":"user@example.com",' +
                '"organization":"test-course-generator",' +
                '"number":"1",' +
                '"run":"1",' +
                '"fields":{"display_name":"test-course"}}'
            )
            call_command("generate_test_course", arg)

    def test_invalid_user(self):
        """
        Test that providing an invalid user will result in the appropriate command error
        """
        error_msg = "User invalid_user not found"
        with self.assertRaisesRegexp(CommandError, error_msg):
            arg = (
                '{"store":"split",' +
                '"user":"invalid_user",' +
                '"organization":"test-course-generator",' +
                '"number":"1",' +
                '"run":"1",' +
                '"fields":{"display_name":"test-course"}}'
            )
            call_command("generate_test_course", arg)
