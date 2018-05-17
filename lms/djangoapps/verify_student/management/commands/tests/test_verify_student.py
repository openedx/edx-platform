"""
Tests for django admin commands in the verify_student module

Lots of imports from verify_student's model tests, since they cover similar ground
"""
import boto
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from mock import patch
from nose.tools import assert_equals

from common.test.utils import MockS3Mixin
from email_marketing.models import EmailMarketingConfiguration
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.tests.test_models import (
    FAKE_SETTINGS,
    mock_software_secure_post,
    mock_software_secure_post_error
)
from student.tests.factories import UserFactory


# Lots of patching to stub in our own settings, and HTTP posting
@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestVerifyStudentCommand(MockS3Mixin, TestCase):
    """
    Tests for django admin commands in the verify_student module
    """
    shard = 4

    def setUp(self):
        super(TestVerifyStudentCommand, self).setUp()
        connection = boto.connect_s3()
        connection.create_bucket(FAKE_SETTINGS['SOFTWARE_SECURE']['S3_BUCKET'])

    def create_and_submit(self, username):
        """
        Helper method that lets us create new SoftwareSecurePhotoVerifications
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        user.profile.name = username
        attempt.upload_face_image("Fake Data")
        attempt.upload_photo_id_image("More Fake Data")
        attempt.mark_ready()
        attempt.submit()
        return attempt

    def test_retry_failed_photo_verifications(self):
        """
        Tests that the task used to find "must_retry" SoftwareSecurePhotoVerifications
        and re-submit them executes successfully
        """
        # set up some fake data to use...
        self.create_and_submit("SuccessfulSally")
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_error):
            self.create_and_submit("RetryRoger")
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_error):
            self.create_and_submit("RetryRick")
        # check to make sure we had two successes and two failures; otherwise we've got problems elsewhere
        assert_equals(len(SoftwareSecurePhotoVerification.objects.filter(status="submitted")), 1)
        assert_equals(len(SoftwareSecurePhotoVerification.objects.filter(status='must_retry')), 2)
        call_command('retry_failed_photo_verifications')
        attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(status='must_retry')
        assert_equals(bool(attempts_to_retry), False)

    @patch('sailthru.sailthru_client.SailthruClient.send')
    @patch(
        'lms.djangoapps.verify_student.management.commands.send_expired_status_emails.IDVerificationService.user_status'
    )
    def test_send_expired_status_email(self, mock_user_status, mock_sailthru_send):
        """
        Tests that the task used to send emails to the learners with expired verification
        statuses executes successfully
        """
        EmailMarketingConfiguration.objects.create(sailthru_verification_expired_template='test_template')
        self.create_and_submit('test_user')
        mock_user_status.return_value = {'status': 'expired'}
        call_command('send_expired_status_emails')
        self.assertTrue(mock_sailthru_send.call_args[1], 'test_template')

    @patch('sailthru.sailthru_client.SailthruClient.send')
    @patch(
        'lms.djangoapps.verify_student.management.commands.send_expired_status_emails.IDVerificationService.user_status'
    )
    def test_expired_status_email_not_sent_to_unexpired_status(self, mock_user_status, mock_sailthru_send):
        """
        Tests that the task is not executed to send emails to the learners with unexpired verification
        """
        EmailMarketingConfiguration.objects.create(sailthru_verification_expired_template='test_template')
        self.create_and_submit('test_user')
        mock_user_status.return_value = {'status': 'other_than_expired'}
        call_command('send_expired_status_emails')
        self.assertFalse(mock_sailthru_send.called)
