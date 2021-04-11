"""
Tests for django admin command `populate_expiration_date` in the verify_student module
"""


from datetime import timedelta

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.utils.timezone import now
from mock import patch
from testfixtures import LogCapture

from common.test.utils import MockS3BotoMixin
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.tests.test_models import FAKE_SETTINGS, mock_software_secure_post
from common.djangoapps.student.tests.factories import UserFactory

LOGGER_NAME = 'lms.djangoapps.verify_student.management.commands.populate_expiration_date'


@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestPopulateExpiryationDate(MockS3BotoMixin, TestCase):
    """ Tests for django admin command `populate_expiration_date` in the verify_student module """

    def create_and_submit(self, user):
        """ Helper method that lets us create new SoftwareSecurePhotoVerifications """
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.upload_face_image("Fake Data")
        attempt.upload_photo_id_image("More Fake Data")
        attempt.mark_ready()
        attempt.submit()
        attempt.expiry_date = now() + timedelta(days=FAKE_SETTINGS["DAYS_GOOD_FOR"])
        return attempt

    def test_no_expiry_date(self):
        """
        Test that the `expiration_date` for most recent approved verification is updated only when the
        deprecated field `expiry_date` is still present
        """
        user = UserFactory.create()
        verification = self.create_and_submit(user)
        verification.status = 'approved'
        verification.expiry_date = None
        verification.save()

        expiration_date = verification.expiration_date
        call_command('populate_expiration_date')

        # Check that the `expiration_date` for approved verification is not changed
        verification_expiration_date = SoftwareSecurePhotoVerification.objects.get(pk=verification.pk).expiration_date

        self.assertEqual(verification_expiration_date, expiration_date)

    def test_no_approved_verification_found(self):
        """
        Test that if no approved verifications are found the management command terminates gracefully
        """
        with LogCapture(LOGGER_NAME) as logger:
            call_command('populate_expiration_date')
            logger.check(
                (LOGGER_NAME, 'INFO', "No approved entries found in SoftwareSecurePhotoVerification")
            )
