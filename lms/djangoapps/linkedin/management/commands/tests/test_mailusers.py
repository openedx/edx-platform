"""
Test email scripts.
"""
import datetime
import json
import mock

from certificates.models import GeneratedCertificate
from django.contrib.auth.models import User
from django.conf import settings
from django.test.utils import override_settings
from django.core import mail
from django.utils.timezone import utc
from django.test import TestCase

from xmodule.modulestore.tests.factories import CourseFactory
from student.models import UserProfile
from xmodule.modulestore.tests.django_utils import mixed_store_config
from linkedin.models import LinkedIn
from linkedin.management.commands import linkedin_mailusers as mailusers

MODULE = 'linkedin.management.commands.linkedin_mailusers.'

TEST_DATA_MIXED_MODULESTORE = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {})


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class MailusersTests(TestCase):
    """
    Test mail users command.
    """

    def setUp(self):
        CourseFactory.create(org='TESTX', number='1', display_name='TEST1',
                             start=datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc),
                             end=datetime.datetime(2011, 5, 12, 2, 42, tzinfo=utc))
        CourseFactory.create(org='TESTX', number='2', display_name='TEST2',
                             start=datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc),
                             end=datetime.datetime(2011, 5, 12, 2, 42, tzinfo=utc))
        CourseFactory.create(org='TESTX', number='3', display_name='TEST3',
                             start=datetime.datetime(2010, 5, 12, 2, 42, tzinfo=utc),
                             end=datetime.datetime(2011, 5, 12, 2, 42, tzinfo=utc))

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
            course_id='TESTX/1/TEST1',
            name='TestX/Intro101',
            download_url='http://test.foo/test')
        cert1.save()
        cert2 = GeneratedCertificate(
            status='downloadable',
            user=fred,
            course_id='TESTX/2/TEST2')
        cert2.save()
        cert3 = GeneratedCertificate(
            status='downloadable',
            user=barney,
            course_id='TESTX/3/TEST3')
        cert3.save()


    @mock.patch.dict('django.conf.settings.LINKEDIN_API',
                     {'EMAIL_WHITELIST': ['barney@bedrock.gov']})
    def test_mail_users_with_whitelist(self):
        """
        Test emailing users.
        """
        fut = mailusers.Command().handle
        fut()
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TESTX/3/TEST3'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].to, ['Barney Rubble <barney@bedrock.gov>'])

    def test_mail_users_grandfather(self):
        """
        Test sending grandfather emails.
        """
        fut = mailusers.Command().handle
        fut()
        self.assertEqual(
            json.loads(self.fred.linkedin.emailed_courses), ['TESTX/1/TEST1', 'TESTX/2/TEST2'])
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), ['TESTX/3/TEST3'])
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(
            mail.outbox[0].to, ['Fred Flintstone <fred@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[0].subject, 'Fred Flintstone, Add your Achievements to your LinkedIn Profile')
        self.assertEqual(
            mail.outbox[1].to, ['Barney Rubble <barney@bedrock.gov>'])
        self.assertEqual(
            mail.outbox[1].subject, 'Barney Rubble, Add your Achievements to your LinkedIn Profile')

    def test_mail_users_grandfather_mock(self):
        """
        test that we aren't sending anything when in mock_run mode
        """
        fut = mailusers.Command().handle
        fut(mock_run=True)
        self.assertEqual(
            json.loads(self.fred.linkedin.emailed_courses), [])
        self.assertEqual(
            json.loads(self.barney.linkedin.emailed_courses), [])
        self.assertEqual(len(mail.outbox), 0)

    def test_certificate_url(self):
        self.cert1.created_date = datetime.datetime(
            2010, 8, 15, 0, 0, tzinfo=utc)
        self.cert1.save()
        fut = mailusers.Command().certificate_url
        self.assertEqual(
            fut(self.cert1),
            'http://www.linkedin.com/profile/guided?'
            'pfCertificationName=TEST1&pfAuthorityName=edX&'
            'pfAuthorityId=0000000&'
            'pfCertificationUrl=http%3A%2F%2Ftest.foo%2Ftest&pfLicenseNo=TESTX%2F1%2FTEST1&'
            'pfCertStartDate=201005&_mSplash=1&'
            'trk=eml-prof-edX-1-gf&startTask=CERTIFICATION_NAME&force=true')
