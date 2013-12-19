"""
Test email scripts.
"""
import json
import mock

from certificates.models import GeneratedCertificate
from django.contrib.auth.models import User
from django.test import TestCase

from student.models import UserProfile
from linkedin.models import LinkedIn
from linkedin.management.commands import linkedin_mailusers as mailusers

MODULE = 'linkedin.management.commands.linkedin_mailusers.'


class MailusersTests(TestCase):
    """
    Test mail users command.
    """

    def setUp(self):
        courses = {
            'TEST1': mock.Mock(org='TestX', number='1'),
            'TEST2': mock.Mock(org='TestX', number='2'),
            'TEST3': mock.Mock(org='TestX', number='3'),
        }
        def get_course_by_id(id):
            return courses.get(id)
        patcher = mock.patch(MODULE + 'get_course_by_id', get_course_by_id)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.fred = fred = User(username='fred')
        fred.save()
        UserProfile(user=fred, name='Fred Flintstone').save()
        LinkedIn(user=fred, has_linkedin_account=True).save()
        self.barney = barney = User(username='barney')
        barney.save()
        LinkedIn(user=barney, has_linkedin_account=True).save()
        UserProfile(user=barney, name='Barney Rubble').save()

        cert1 = GeneratedCertificate(
            status='downloadable',
            user=fred,
            course_id='TEST1')
        cert1.save()
        cert2 = GeneratedCertificate(
            status='downloadable',
            user=fred,
            course_id='TEST2')
        cert2.save()
        cert3 = GeneratedCertificate(
            status='downloadable',
            user=barney,
            course_id='TEST3')
        cert3.save()

    def test_mail_users(self):
        """
        Test emailing users.
        """
        fut = mailusers.Command().handle
        fut()
        self.assertEqual(
            json.loads(self.fred.linkedin.emailed_courses), ['TEST1', 'TEST2'])
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TEST3'])

    def test_mail_users_grandfather(self):
        """
        Test sending grandfather emails.
        """
        fut = mailusers.Command().handle
        fut(grandfather=True)
        self.assertEqual(
            json.loads(self.fred.linkedin.emailed_courses), ['TEST1', 'TEST2'])
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TEST3'])

    def test_mail_users_only_new_courses(self):
        """
        Test emailing users, making sure they are only emailed about new
        certificates.
        """
        self.fred.linkedin.emailed_courses = json.dumps(['TEST1'])
        self.fred.linkedin.save()
        fut = mailusers.Command().handle
        fut()
        fred = User.objects.get(username='fred')
        self.assertEqual(
            json.loads(fred.linkedin.emailed_courses), ['TEST1', 'TEST2'])
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TEST3'])
