"""
Test for generate_report command.
"""

from io import StringIO

from django.core.management import call_command
from django.test import TestCase


class GenerateReportTest(TestCase):
    def test_command_output(self):
        out = StringIO()
        call_command('generate_report', stdout=out)
        self.assertIn('Survey report has been generated successfully.', out.getvalue())
