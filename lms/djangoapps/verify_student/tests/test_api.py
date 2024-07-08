"""
Tests of API module.
"""
from unittest.mock import patch

import ddt
from django.conf import settings
from django.core import mail
from django.test import TestCase

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.verify_student.api import send_approval_email
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification


@ddt.ddt
class TestSendApprovalEmail(TestCase):
    """
    Test cases for the send_approval_email API method.
    """
    def setUp(self):
        super().setUp()

        self.user = UserFactory.create()
        self.attempt = SoftwareSecurePhotoVerification(
            status="submitted",
            user=self.user
        )
        self.attempt.save()

    def _assert_verification_approved_email(self, expiration_date):
        """Check that a verification approved email was sent."""
        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.subject == 'Your édX ID verification was approved!'
        assert 'Your édX ID verification photos have been approved' in email.body
        assert expiration_date.strftime("%m/%d/%Y") in email.body

    @ddt.data(True, False)
    def test_send_approval(self, use_ace):
        with patch.dict(settings.VERIFY_STUDENT, {'USE_DJANGO_MAIL': use_ace}):
            send_approval_email(self.attempt)
            self._assert_verification_approved_email(self.attempt.expiration_datetime)
