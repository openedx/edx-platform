"""
Test email scripts.
"""
import json
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
        Test emailing users.
        """
        fut = mailusers.Command().handle
        cert1 = mock.Mock(course_id=1)
        cert2 = mock.Mock(course_id=2)
        cert3 = mock.Mock(course_id=3)
        fred = mock.Mock(
            emailed_courses="[]",
            user=mock.Mock(certificates=[cert1, cert2]))
        barney = mock.Mock(
            emailed_courses="[]",
            user=mock.Mock(certificates=[cert3]))
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
            [((fred.user, cert1),),
             ((fred.user, cert2),),
             ((barney.user, cert3),)])
        self.assertEqual(json.loads(fred.emailed_courses), [1, 2])
        self.assertEqual(json.loads(barney.emailed_courses), [3])

    @mock.patch('linkedin.management.commands.mailusers.send_grandfather_email')
    @mock.patch('linkedin.management.commands.mailusers.GeneratedCertificate')
    @mock.patch('linkedin.management.commands.mailusers.LinkedIn')
    def test_mail_users_grandfather(self, linkedin, certificates, send_email):
        """
        Test sending grandfather emails.
        """
        fut = mailusers.Command().handle
        cert1 = mock.Mock(course_id=1)
        cert2 = mock.Mock(course_id=2)
        cert3 = mock.Mock(course_id=3)
        fred = mock.Mock(
            emailed_courses="[]",
            user=mock.Mock(certificates=[cert1, cert2]))
        barney = mock.Mock(
            emailed_courses="[]",
            user=mock.Mock(certificates=[cert3]))
        linkedin.objects.filter.return_value = [fred, barney]

        def filter_user(user):
            "Mock querying the database."
            queryset = mock.Mock()
            queryset.filter.return_value = user.certificates
            return queryset

        certificates.objects.filter = filter_user
        fut(grandfather=True)
        self.assertEqual(
            send_email.call_args_list,
            [((fred.user, [cert1, cert2]),),
             ((barney.user, [cert3]),)])
        self.assertEqual(json.loads(fred.emailed_courses), [1, 2])
        self.assertEqual(json.loads(barney.emailed_courses), [3])

    @mock.patch('linkedin.management.commands.mailusers.send_email')
    @mock.patch('linkedin.management.commands.mailusers.GeneratedCertificate')
    @mock.patch('linkedin.management.commands.mailusers.LinkedIn')
    def test_mail_users_only_new_courses(self, linkedin, certificates,
                                         send_email):
        """
        Test emailing users, making sure they are only emailed about new
        certificates.
        """
        fut = mailusers.Command().handle
        cert1 = mock.Mock(course_id=1)
        cert2 = mock.Mock(course_id=2)
        cert3 = mock.Mock(course_id=3)
        fred = mock.Mock(
            emailed_courses="[1]",
            user=mock.Mock(certificates=[cert1, cert2]))
        barney = mock.Mock(
            emailed_courses="[]",
            user=mock.Mock(certificates=[cert3]))
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
            [((fred.user, cert2),),
             ((barney.user, cert3),)])
        self.assertEqual(json.loads(fred.emailed_courses), [1, 2])
        self.assertEqual(json.loads(barney.emailed_courses), [3])
