"""
Tests for django admin commands in the verify_student module

Lots of imports from verify_student's model tests, since they cover similar ground
"""

from django.conf import settings
from django.core.management import call_command
from mock import patch
from testfixtures import LogCapture

from common.test.utils import MockS3BotoMixin
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSPVerificationRetryConfig
from lms.djangoapps.verify_student.tests import TestVerificationBase
from lms.djangoapps.verify_student.tests.test_models import (
    FAKE_SETTINGS,
    mock_software_secure_post,
    mock_software_secure_post_error
)
from common.djangoapps.student.tests.factories import UserFactory  # pylint: disable=import-error, useless-suppression

LOGGER_NAME = 'retry_photo_verification'


# Lots of patching to stub in our own settings, and HTTP posting
@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestVerifyStudentCommand(MockS3BotoMixin, TestVerificationBase):
    """
    Tests for django admin commands in the verify_student module
    """

    def test_retry_failed_photo_verifications(self):
        """
        Tests that the task used to find "must_retry" SoftwareSecurePhotoVerifications
        and re-submit them executes successfully
        """
        # set up some fake data to use...
        self.create_upload_and_submit_attempt_for_user()
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_error):
            self.create_upload_and_submit_attempt_for_user()
            self.create_upload_and_submit_attempt_for_user()

        # check to make sure we had two successes and two failures; otherwise we've got problems elsewhere
        self.assertEqual(SoftwareSecurePhotoVerification.objects.filter(status="submitted").count(), 1)
        self.assertEqual(SoftwareSecurePhotoVerification.objects.filter(status='must_retry').count(), 2)

        with self.immediate_on_commit():
            call_command('retry_failed_photo_verifications')
        attempts_to_retry = SoftwareSecurePhotoVerification.objects.filter(status='must_retry')
        assert not attempts_to_retry

    def add_test_config_for_retry_verification(self):
        """Setups verification retry configuration."""
        config = SSPVerificationRetryConfig.current()
        config.arguments = '--verification-ids 1 2 3'
        config.enabled = True
        config.save()

    def test_args_from_database(self):
        """Test management command arguments injected from config model."""
        # Nothing in the database, should default to disabled
        with LogCapture(LOGGER_NAME) as log:
            call_command('retry_failed_photo_verifications', '--args-from-database')
            log.check_present(
                (
                    LOGGER_NAME, 'WARNING',
                    'SSPVerificationRetryConfig is disabled or empty, but --args-from-database was requested.'
                ),
            )
        self.add_test_config_for_retry_verification()
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_error):
            self.create_upload_and_submit_attempt_for_user()
            with LogCapture(LOGGER_NAME) as log:
                with self.immediate_on_commit():
                    call_command('retry_failed_photo_verifications')
                    log.check_present(
                        (
                            LOGGER_NAME, 'INFO',
                            'Attempting to retry {0} failed PhotoVerification submissions'.format(1)
                        ),
                    )

        with LogCapture(LOGGER_NAME) as log:
            with self.immediate_on_commit():
                call_command('retry_failed_photo_verifications', '--args-from-database')

                log.check_present(
                    (
                        LOGGER_NAME, 'INFO',
                        'Fetching retry verification ids from config model'
                    ),
                )
