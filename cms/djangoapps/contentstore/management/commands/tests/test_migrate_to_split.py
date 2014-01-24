"""
Unittests for importing a course via management command
"""

import unittest

from django.core.management import CommandError
from contentstore.management.commands.migrate_to_split import Command


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
        errstring = "No user exists with ID 99"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("i4x://org/course/category/name", "99")

    def test_nonexistant_user_email(self):
        errstring = "No user exists with email fake@example.com"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle("i4x://org/course/category/name", "fake@example.com")
