"""
Tests for django admin command `populate_expiry_date` in the verify_student module
"""


from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from mock import patch
from testfixtures import LogCapture

from common.test.utils import MockS3BotoMixin
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.tests.test_models import FAKE_SETTINGS, mock_software_secure_post
from common.djangoapps.student.tests.factories import UserFactory

LOGGER_NAME = 'lms.djangoapps.verify_student.management.commands.populate_expiry_date'


@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestPopulateExpiryDate(MockS3BotoMixin, TestCase):
    """ Tests for django admin command `populate_expiry_date` in the verify_student module """

    def create_and_submit(self, user):
        """ Helper method that lets us create new SoftwareSecurePhotoVerifications """
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.upload_face_image("Fake Data")
        attempt.upload_photo_id_image("More Fake Data")
        attempt.mark_ready()
        attempt.submit()
        return attempt

    def test_expiry_date_already_present(self):
        """
        Test that the expiry_date for most recent approved verification is updated only when the
        expiry_date is not already present
        """
        user = UserFactory.create()
        verification = self.create_and_submit(user)
        verification.status = 'approved'
        verification.expiry_date = verification.updated_at + timedelta(days=10)
        verification.save()

        expiry_date = verification.expiry_date
        call_command('populate_expiry_date')

        # Check that the expiry_date for approved verification is not changed when it is already present
        verification_expiry_date = SoftwareSecurePhotoVerification.objects.get(pk=verification.pk).expiry_date

        self.assertEqual(verification_expiry_date, expiry_date)

    def test_recent_approved_verification(self):
        """
        Test that the expiry_date for most recent approved verification is updated
        A user can have multiple approved Software Secure Photo Verification over the year
        Only the most recent is considered for course verification
        """
        user = UserFactory.create()
        outdated_verification = self.create_and_submit(user)
        outdated_verification.status = 'approved'
        outdated_verification.save()

        recent_verification = self.create_and_submit(user)
        recent_verification.status = 'approved'
        recent_verification.save()

        call_command('populate_expiry_date')

        # Check that expiry_date for only one verification is set
        assert len(SoftwareSecurePhotoVerification.objects.filter(expiry_date__isnull=False)) == 1

        # Check that the expiry_date date set for verification is not for the outdated approved verification
        expiry_date = SoftwareSecurePhotoVerification.objects.get(pk=outdated_verification.pk).expiry_date
        self.assertIsNone(expiry_date)

    def test_approved_verification_expiry_date(self):
        """
        Tests that the command correctly updates expiry_date
        Criteria :
                 Verification for which status is approved and expiry_date is null
        """
        # Create verification with status : submitted
        user = UserFactory.create()
        self.create_and_submit(user)

        # Create verification with status : approved
        approved_verification = self.create_and_submit(user)
        approved_verification.status = 'approved'
        approved_verification.save()

        expected_date = approved_verification.updated_at + timedelta(
            days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])

        call_command('populate_expiry_date')

        # Check to make sure we have one verification with expiry_date set and one with null
        assert len(SoftwareSecurePhotoVerification.objects.filter(expiry_date__isnull=True)) == 1
        assert len(SoftwareSecurePhotoVerification.objects.filter(expiry_date__isnull=False)) == 1

        # Confirm that expiry_date set for approved verification is correct
        approved_verification = SoftwareSecurePhotoVerification.objects.get(pk=approved_verification.pk)
        self.assertEqual(approved_verification.expiry_date, expected_date)

    def test_no_approved_verification_found(self):
        """
        Test that if no approved verifications are found the management command terminates gracefully
        """
        with LogCapture(LOGGER_NAME) as logger:
            call_command('populate_expiry_date')
            logger.check(
                (LOGGER_NAME, 'INFO', "No approved entries found in SoftwareSecurePhotoVerification")
            )
