"""Test Tahoe API Django management commands

"""

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from student.tests.factories import UserFactory


class TahoeCreateTokenTest(TestCase):
    """Tests the management command to get or create a token for a user

    """
    def test_command_output(self):
        username = 'mr_robot'
        UserFactory(username=username)
        out = StringIO()
        call_command('tahoe_create_token', username, stdout=out)
        outvals = out.getvalue().split('\n')
        self.assertEqual(len(outvals), 3)
        self.assertEqual(outvals[0][:10], 'token key:')
        self.assertEqual(outvals[1], 'user: "{}"'.format(username))
        self.assertEqual(outvals[2], '')
