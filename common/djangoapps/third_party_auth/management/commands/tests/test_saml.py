"""
Tests for `saml` management command, this command fetches saml metadata from providers and updates
existing data accordingly.
"""
import unittest

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.conf import settings


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestSAMLCommand(TestCase):
    """
    Test django management command for fetching saml metadata.
    """
    def test_raises_command_error_for_invalid_arguments(self):
        """
        Test that management command raises `CommandError` with a proper message in case of
        invalid command arguments.

        This test would fail with an error if ValueError is raised.
        """
        # Call `saml` command without any argument so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command can only be used with '--pull' option."):
            call_command("saml")

        # Call `saml` command without any argument so that it raises a CommandError
        with self.assertRaisesMessage(CommandError, "Command can only be used with '--pull' option."):
            call_command("saml", pull=False)
