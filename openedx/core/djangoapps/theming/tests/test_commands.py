"""
Tests for Management commands of comprehensive theming.
"""
from django.test import TestCase
from django.core.management import call_command, CommandError

from openedx.core.djangoapps.theming.helpers import get_themes
from openedx.core.djangoapps.theming.management.commands.compile_sass import Command


class TestUpdateAssets(TestCase):
    """
    Test comprehensive theming helper functions.
    """
    def setUp(self):
        super(TestUpdateAssets, self).setUp()
        self.themes = get_themes()

    def test_errors_for_invalid_arguments(self):
        """
        Test update_asset command.
        """
        # make sure error is raised for invalid theme list
        with self.assertRaises(CommandError):
            call_command("compile_sass", themes=["all", "test-theme"])

        # make sure error is raised for invalid theme list
        with self.assertRaises(CommandError):
            call_command("compile_sass", themes=["no", "test-theme"])

        # make sure error is raised for invalid theme list
        with self.assertRaises(CommandError):
            call_command("compile_sass", themes=["all", "no"])

        # make sure error is raised for invalid theme list
        with self.assertRaises(CommandError):
            call_command("compile_sass", themes=["test-theme", "non-existing-theme"])

    def test_parse_arguments(self):
        """
        Test parse arguments method for update_asset command.
        """
        # make sure compile_sass picks all themes when called with 'themes=all' option
        parsed_args = Command.parse_arguments(themes=["all"])
        self.assertItemsEqual(parsed_args[2], get_themes())

        # make sure compile_sass picks no themes when called with 'themes=no' option
        parsed_args = Command.parse_arguments(themes=["no"])
        self.assertItemsEqual(parsed_args[2], [])

        # make sure compile_sass picks only specified themes
        parsed_args = Command.parse_arguments(themes=["test-theme"])
        self.assertItemsEqual(parsed_args[2], [theme for theme in get_themes() if theme.theme_dir_name == "test-theme"])
