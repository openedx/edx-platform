"""  # lint-amnesty, pylint: disable=cyclic-import
Tests for django admin commands in the verify_student module

"""
import ddt
import logging
import os
import tempfile

import pytest
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import TestCase
from testfixtures import LogCapture

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification

LOGGER_NAME = 'lms.djangoapps.verify_student.management.commands.approve_id_verifications'


@ddt.ddt
class TestApproveIDVerificationsCommand(TestCase):
    """
    Tests for django admin commands in the verify_student module
    """
    tmp_file_path = os.path.join(tempfile.gettempdir(), 'tmp-user-ids.txt')

    def setUp(self):
        super().setUp()
        self.user1_profile = UserProfileFactory.create(user=UserFactory.create())
        self.user2_profile = UserProfileFactory.create(user=UserFactory.create())
        self.user3_profile = UserProfileFactory.create(user=UserFactory.create())
        self.invalid_user_id = '12345'

        self.create_user_ids_file(
            self.tmp_file_path,
            [
                str(self.user1_profile.id),
                str(self.user2_profile.id),
                str(self.user3_profile.id),
                str(self.invalid_user_id),
                'invalid_user_id',
            ]
        )

    @staticmethod
    def create_user_ids_file(file_path, user_ids):
        """
        Write the email_ids list to the temp file.
        """
        with open(file_path, 'w') as temp_file:
            temp_file.write(str("\n".join(user_ids)))

    @ddt.data('submitted', 'must_retry')
    def test_approve_id_verifications(self, status):
        """
        Tests that the approve_id_verifications management command executes successfully.
        """
        # Create SoftwareSecurePhotoVerification instances for the users.
        for user in [self.user1_profile, self.user2_profile, self.user3_profile]:
            SoftwareSecurePhotoVerification.objects.create(
                user=user.user,
                name=user.name,
                status=status,
            )

        assert SoftwareSecurePhotoVerification.objects.filter(status='approved').count() == 0

        call_command('approve_id_verifications', self.tmp_file_path)

        assert SoftwareSecurePhotoVerification.objects.filter(status='approved').count() == 3

    @ddt.data('submitted', 'must_retry')
    def test_approve_id_verifications_email(self, status):
        """
        Tests that the approve_id_verifications management command correctly sends approval emails.
        """
        # Create SoftwareSecurePhotoVerification instances for the users.
        for user in [self.user1_profile, self.user2_profile]:
            SoftwareSecurePhotoVerification.objects.create(
                user=user.user,
                name=user.name,
                status=status,
            )
        SoftwareSecurePhotoVerification.objects.create(
            user=self.user3_profile.user,
            name=self.user3_profile.name,
            status='denied',
        )

        call_command('approve_id_verifications', self.tmp_file_path)

        assert len(mail.outbox) == 2

        # All three emails should have equal expiration dates, so just pick one from an attempt.
        expiration_date = SoftwareSecurePhotoVerification.objects.first().expiration_datetime
        for email in mail.outbox:
            assert email.subject == 'Your édX ID verification was approved!'
            assert 'Your édX ID verification photos have been approved' in email.body
            assert expiration_date.strftime("%m/%d/%Y") in email.body

    def test_user_does_not_exist_log(self):
        """
        Tests that the approve_id_verifications management command logs an error when an invalid user ID is
        provided as input.
        """
        expected_log = (
            (LOGGER_NAME,
             'INFO',
             'Received request to manually approve ID verification attempts for 5 users.'
             ),
            (LOGGER_NAME,
             'INFO',
             'Skipping user ID invalid_user_id, invalid user ID.'
             ),
            (LOGGER_NAME,
             'INFO',
             'Attempting to manually approve ID verification attempts for 4 users.'
             ),
            (LOGGER_NAME,
             'INFO',
             'Skipping user ID 3, either no user or no IDV verification attempt found.'
             ),
            (LOGGER_NAME,
             'INFO',
             'Skipping user ID 12345, either no user or no IDV verification attempt found.'
             ),
            (LOGGER_NAME,
             'ERROR',
             'Completed ID verification approvals. 2 of 4 failed.',
             ),
            (LOGGER_NAME,
             'ERROR',
             f"Failed user IDs:[{self.user3_profile.user.id}, {self.invalid_user_id}]"
             )
        )

        # Create SoftwareSecurePhotoVerification instances for the users.
        for user in [self.user1_profile, self.user2_profile]:
            SoftwareSecurePhotoVerification.objects.create(
                user=user.user,
                name=user.name,
                status='submitted',
            )

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('approve_id_verifications', self.tmp_file_path)

            logger.check_present(
                *expected_log,
                order_matters=False,
            )

    def test_invalid_file_path(self):
        """
        Verify command raises the CommandError for invalid file path.
        """
        with pytest.raises(CommandError):
            call_command('approve_id_verifications', 'invalid/user_id/file/path')
