"""
Test `massemail` and `massemailtxt` commands.
"""
import mock
import pkg_resources

from django.core import mail
from django.test import TestCase

from edxmako import add_lookup
from ..management.commands import massemail
from ..management.commands import massemailtxt


class TestMassEmailCommands(TestCase):
    """
    Test `massemail` and `massemailtxt` commands.
    """

    @mock.patch('edxmako.LOOKUP', {})
    def test_massemailtxt(self):
        """
        Test the `massemailtext` command.
        """
        add_lookup('main', '', package=__name__)
        userfile = pkg_resources.resource_filename(__name__, 'test_massemail_users.txt')
        command = massemailtxt.Command()
        command.handle(userfile, 'test', '/dev/null', 10)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["Fred"])
        self.assertEqual(mail.outbox[0].subject, "Test subject.")
        self.assertEqual(mail.outbox[0].body.strip(), "Test body.")
        self.assertEqual(mail.outbox[1].to, ["Barney"])
        self.assertEqual(mail.outbox[1].subject, "Test subject.")
        self.assertEqual(mail.outbox[1].body.strip(), "Test body.")

    @mock.patch('edxmako.LOOKUP', {})
    @mock.patch('student.management.commands.massemail.User')
    def test_massemail(self, usercls):
        """
        Test the `massemail` command.
        """
        add_lookup('main', '', package=__name__)
        fred = mock.Mock()
        barney = mock.Mock()
        usercls.objects.all.return_value = [fred, barney]
        command = massemail.Command()
        command.handle('test')
        fred.email_user.assert_called_once_with('Test subject.', 'Test body.\n')
        barney.email_user.assert_called_once_with('Test subject.', 'Test body.\n')
