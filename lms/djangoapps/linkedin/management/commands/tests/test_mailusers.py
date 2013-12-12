"""
Test email scripts.
"""
import mock
import unittest

from linkedin.management.commands import mailusers


class MailusersTests(unittest.TestCase):
    """
    Test mail users command.
    """

    @mock.patch('linkedin.management.commands.mailusers.send_email')
    @mock.patch('linkedin.management.commands.mailusers.GeneratedCertificate')
    @mock.patch('linkedin.management.commands.mailusers.LinkedIn')
    def test_mail_users(self, linkedin, certificates, send_email):
        """
        Test "happy path" for emailing users.
        """
        fut = mailusers.Command().handle
        fred = mock.Mock(user=mock.Mock(certificates=[1, 2]))
        barney = mock.Mock(user=mock.Mock(certificates=[3]))
        linkedin.objects.filter.return_value = [fred, barney]

        def filter_user(user):
            "Mock querying the database."
            queryset = mock.Mock()
            queryset.filter.return_value = user.certificates
            return queryset

        certificates.objects.filter = filter_user
        fut()
        self.assertEqual(
            send_email.call_args_list,
            [((fred.user, 1),),
             ((fred.user, 2),),
             ((barney.user, 3),)])
