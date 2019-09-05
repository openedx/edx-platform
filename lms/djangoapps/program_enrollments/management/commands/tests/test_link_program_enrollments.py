"""
Tests for the link_program_enrollments management command.
"""
from __future__ import absolute_import

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from lms.djangoapps.program_enrollments.tests.test_link_program_enrollments import TestLinkProgramEnrollmentsMixin
from lms.djangoapps.program_enrollments.management.commands.link_program_enrollments import (
    Command,
    INCORRECT_PARAMETER_TPL,
    DUPLICATE_KEY_TPL,
)

COMMAND_PATH = 'lms.djangoapps.program_enrollments.management.commands.link_program_enrollments'


class TestLinkProgramEnrollmentManagementCommand(TestLinkProgramEnrollmentsMixin, TestCase):
    """ Tests for exception behavior in the link_program_enrollments command """

    def test_incorrectly_formatted_input(self):
        with self.assertRaisesRegex(CommandError, INCORRECT_PARAMETER_TPL.format('whoops')):
            call_command(Command(), self.program, 'learner-01:user-01', 'whoops', 'learner-03:user-03')

    def test_repeated_user_key(self):
        with self.assertRaisesRegex(CommandError, DUPLICATE_KEY_TPL.format('learner-01')):
            call_command(Command(), self.program, 'learner-01:user-01', 'learner-01:user-02')
