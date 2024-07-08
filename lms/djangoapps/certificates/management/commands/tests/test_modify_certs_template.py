"""
Tests for the modify_cert_template command
"""

import pytest
from django.core.management import CommandError, call_command
from django.test import TestCase


class ModifyCertTemplateTests(TestCase):
    """Tests for the modify_cert_template management command"""

    def test_command_with_missing_param_old_text(self):
        """Verify command with a missing param --old-text."""
        with pytest.raises(
            CommandError,
            match="The following arguments are required: --old-text, --new-text, --templates",
        ):
            call_command(
                "modify_cert_template", "--new-text", "blah", "--templates", "1 2 3"
            )

    def test_command_with_missing_param_new_text(self):
        """Verify command with a missing param --new-text."""
        with pytest.raises(
            CommandError,
            match="The following arguments are required: --old-text, --new-text, --templates",
        ):
            call_command(
                "modify_cert_template", "--old-text", "blah", "--templates", "1 2 3"
            )

    def test_command_with_missing_param_templates(self):
        """Verify command with a missing param --templates."""
        with pytest.raises(
            CommandError,
            match="The following arguments are required: --old-text, --new-text, --templates",
        ):
            call_command(
                "modify_cert_template", "--new-text", "blah", "--old-text", "xyzzy"
            )
