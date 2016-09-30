"""
Tests for django admin commands in the verify_student module

Lots of imports from verify_student's model tests, since they cover similar ground
"""
from nose.tools import assert_equals
from mock import patch

from django.test import TestCase
from django.conf import settings

from student.tests.factories import UserFactory
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from django.core.management import call_command
from lms.djangoapps.verify_student.tests.test_models import (
    MockKey, MockS3Connection, mock_software_secure_post,
    mock_software_secure_post_error, FAKE_SETTINGS,
)


# Lots of patching to stub in our own settings, S3 substitutes, and HTTP posting
@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.S3Connection', new=MockS3Connection)
@patch('lms.djangoapps.verify_student.models.Key', new=MockKey)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestVerifyStudentCommand(TestCase):
    """
    Tests for django admin commands in the verify_student module
    """

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
