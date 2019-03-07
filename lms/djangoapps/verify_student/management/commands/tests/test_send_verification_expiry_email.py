"""
Tests for django admin command `send_verification_expiry_email` in the verify_student module
"""

from datetime import datetime, timedelta

import boto
from django.conf import settings
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from mock import patch
from pytz import UTC
from student.tests.factories import UserFactory
from testfixtures import LogCapture

from common.test.utils import MockS3Mixin
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.tests.test_models import (
    FAKE_SETTINGS,
    mock_software_secure_post
)

LOGGER_NAME = 'lms.djangoapps.verify_student.management.commands.send_verification_expiry_email'


@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestSendVerificationExpiryEmail(MockS3Mixin, TestCase):
    """ Tests for django admin command `send_verification_expiry_email` in the verify_student module """

    def setUp(self):
        """ Initial set up for tests """
        super(TestSendVerificationExpiryEmail, self).setUp()
        connection = boto.connect_s3()
        connection.create_bucket(FAKE_SETTINGS['SOFTWARE_SECURE']['S3_BUCKET'])
        Site.objects.create(domain='edx.org', name='edx.org')

    def create_and_submit(self, user):
        """ Helper method that lets us create new SoftwareSecurePhotoVerifications """
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.upload_face_image("Fake Data")
        attempt.upload_photo_id_image("More Fake Data")
        attempt.mark_ready()
        attempt.submit()
        return attempt

    def test_expiry_date_range(self):
        """
        Test that the verifications are filtered on the given range. Email is not sent for any verification with
        expiry date out of range
        """
        user = UserFactory.create()
        verification_in_range = self.create_and_submit(user)
        verification_in_range.status = 'approved'
        verification_in_range.expiry_date = datetime.now(UTC) - timedelta(days=1)
        verification_in_range.save()

        user = UserFactory.create()
        verification = self.create_and_submit(user)
        verification.status = 'approved'
        verification.expiry_date = datetime.now(UTC) - timedelta(days=5)
        verification.save()

        call_command('send_verification_expiry_email', '--days-range=2')

        # Check that only one email is sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the email is not sent to the out of range verification
        expiry_email_date = SoftwareSecurePhotoVerification.objects.get(pk=verification.pk).expiry_email_date
        self.assertIsNone(expiry_email_date)

    def test_expiry_email_date_range(self):
        """
        Test that the verifications are filtered if the expiry_email_date has reached the time specified for
        resending email
        """
        user = UserFactory.create()
        verification_in_range = self.create_and_submit(user)
        verification_in_range.status = 'approved'
        verification_in_range.expiry_date = datetime.now(UTC) - timedelta(days=30)
        verification_in_range.expiry_email_date = datetime.now(UTC) - timedelta(days=3)
        verification_in_range.save()

        command_args = '--days-range={} --resend-days={}'  # pylint: disable=unicode-format-string
        call_command('send_verification_expiry_email', *command_args.format(2, 2).split(' '))

        # Check that email is sent even if the verification is not in expiry_date range but matches the criteria
        # to resend email
        self.assertEqual(len(mail.outbox), 1)

    def test_most_recent_verification(self):
        """
        Test that the SoftwareSecurePhotoVerification object is not filtered if it is outdated. A verification is
        outdated if it's expiry_date and expiry_email_date is set NULL
        """
        # For outdated verification the expiry_date and expiry_email_date is set NULL verify_student/views.py:1164
        user = UserFactory.create()
        outdated_verification = self.create_and_submit(user)
        outdated_verification.status = 'approved'
        outdated_verification.save()

        # Check that the expiry_email_date is not set for the outdated verification
        expiry_email_date = SoftwareSecurePhotoVerification.objects.get(pk=outdated_verification.pk).expiry_email_date
        self.assertIsNone(expiry_email_date)

    def test_send_verification_expiry_email(self):
        """
        Test that checks for valid criteria the email is sent and expiry_email_date is set
        """
        user = UserFactory.create()
        verification = self.create_and_submit(user)
        verification.status = 'approved'
        verification.expiry_date = datetime.now(UTC) - timedelta(days=1)
        verification.save()

        call_command('send_verification_expiry_email')

        expected_date = datetime.now(UTC)
        attempt = SoftwareSecurePhotoVerification.objects.get(user_id=verification.user_id)
        self.assertEquals(attempt.expiry_email_date.date(), expected_date.date())
        self.assertEqual(len(mail.outbox), 1)

    def test_email_already_sent(self):
        """
        Test that if email is already sent as indicated by expiry_email_date then don't send again if it has been less
        than resend_days
        """
        user = UserFactory.create()
        verification = self.create_and_submit(user)
        verification.status = 'approved'
        verification.expiry_date = datetime.now(UTC) - timedelta(days=1)
        verification.expiry_email_date = datetime.now()
        verification.save()

        call_command('send_verification_expiry_email')

        self.assertEqual(len(mail.outbox), 0)

    def test_no_verification_found(self):
        """
        Test that if no approved and expired verifications are found the management command terminates gracefully
        """
        start_date = datetime.now(UTC) - timedelta(days=1)  # using default days
        with LogCapture(LOGGER_NAME) as logger:
            call_command('send_verification_expiry_email')
            logger.check(
                (LOGGER_NAME,
                 'INFO', u"No approved expired entries found in SoftwareSecurePhotoVerification for the "
                         u"date range {} - {}".format(start_date.date(), datetime.now(UTC).date()))
            )

    def test_dry_run_flag(self):
        """
        Test that the dry run flags sends no email and only logs the the number of email sent in each batch
        """
        user = UserFactory.create()
        verification = self.create_and_submit(user)
        verification.status = 'approved'
        verification.expiry_date = datetime.now(UTC) - timedelta(days=1)
        verification.save()

        start_date = datetime.now(UTC) - timedelta(days=1)  # using default days
        count = 1

        with LogCapture(LOGGER_NAME) as logger:
            call_command('send_verification_expiry_email', '--dry-run')
            logger.check(
                (LOGGER_NAME,
                 'INFO',
                 u"For the date range {} - {}, total Software Secure Photo verification filtered are {}"
                 .format(start_date.date(), datetime.now(UTC).date(), count)
                 ),
                (LOGGER_NAME,
                 'INFO',
                 u"This was a dry run, no email was sent. For the actual run email would have been sent "
                 u"to {} learner(s)".format(count)
                 ))
        self.assertEqual(len(mail.outbox), 0)
