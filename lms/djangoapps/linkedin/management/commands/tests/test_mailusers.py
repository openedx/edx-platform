"""
Test email scripts.
"""
import datetime
import json
import mock

from certificates.models import GeneratedCertificate
from django.contrib.auth.models import User
from django.core import mail
from django.utils.timezone import utc
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
            'TEST1': mock.Mock(
                org='TestX', number='1',
                start=datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc)),
            'TEST2': mock.Mock(org='TestX', number='2'),
            'TEST3': mock.Mock(org='TestX', number='3'),
        }
        def get_course_by_id(id):
            return courses.get(id)
        patcher = mock.patch(MODULE + 'get_course_by_id', get_course_by_id)
        patcher.start()
        self.addCleanup(patcher.stop)

        self.fred = fred = User(username='fred', email='fred@bedrock.gov')
        fred.save()
        UserProfile(user=fred, name='Fred Flintstone').save()
        LinkedIn(user=fred, has_linkedin_account=True).save()
        self.barney = barney = User(
            username='barney', email='barney@bedrock.gov')
        barney.save()
        LinkedIn(user=barney, has_linkedin_account=True).save()
        UserProfile(user=barney, name='Barney Rubble').save()

        self.cert1 = cert1 = GeneratedCertificate(
            status='downloadable',
            user=fred,
            course_id='TEST1',
            name='TestX/Intro101',
            download_url='http://test.foo/test')
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
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[0].from_email, 'The Team <team@test.foo>')
        self.assertEqual(
            mail.outbox[0].to, ['Fred Flintstone <fred@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[1].to, ['Fred Flintstone <fred@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[2].to, ['Barney Rubble <barney@bedrock.gov>'])

    @mock.patch.dict('django.conf.settings.LINKEDIN_API',
                     {'EMAIL_WHITELIST': ['barney@bedrock.gov']})
    def test_mail_users_with_whitelist(self):
        """
        Test emailing users.
        """
        fut = mailusers.Command().handle
        fut()
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TEST3'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to, ['Barney Rubble <barney@bedrock.gov>'])

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
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].to, ['Fred Flintstone <fred@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[1].to, ['Barney Rubble <barney@bedrock.gov>'])

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
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].to, ['Fred Flintstone <fred@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[1].to, ['Barney Rubble <barney@bedrock.gov>'])

    def test_mail_users_barney_has_no_new_courses(self):
        """
        Test emailing users, making sure they are only emailed about new
        certificates.
        """
        self.barney.linkedin.emailed_courses = json.dumps(['TEST3'])
        self.barney.linkedin.save()
        fut = mailusers.Command().handle
        fut()
        fred = User.objects.get(username='fred')
        self.assertEqual(
            json.loads(fred.linkedin.emailed_courses), ['TEST1', 'TEST2'])
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TEST3'])
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].to, ['Fred Flintstone <fred@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[1].to, ['Fred Flintstone <fred@bedrock.gov>'])

    def test_certificate_url(self):
        self.cert1.created_date = datetime.datetime(
            2010, 8, 15, 0, 0, tzinfo=utc)
        self.cert1.save()
        fut = mailusers.Command().certificate_url
        self.assertEqual(fut(self.cert1),
            'http://www.linkedin.com/profile/guided?'
            'pfCertificationName=TestX%2FIntro101&pfAuthorityName=edX&'
            'pfAuthorityId=0000000&'
            'pfCertificationUrl=http%3A%2F%2Ftest.foo%2Ftest&pfLicenseNo=TEST1&'
            'pfCertStartDate=201005I&pfCertFuture=201008&_mSplash=1&'
            'trk=eml-prof-TestX-1-T&startTask=CERTIFICATION_NAME&force=true')
