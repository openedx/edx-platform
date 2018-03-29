# -*- coding: utf-8 -*-
"""
Tests for verify_student utility functions.
"""

from datetime import datetime, timedelta

import unittest
import pytz
from mock import patch
from pytest import mark
from django.conf import settings
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.utils import verification_for_datetime
from student.tests.factories import UserFactory

FAKE_SETTINGS = {
    "DAYS_GOOD_FOR": 10,
}


@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@mark.django_db
class TestVerifyStudentUtils(unittest.TestCase):
    """
    Tests for utility functions in verify_student.
    """

    def test_verification_for_datetime(self):
        user = UserFactory.create()
        now = datetime.now(pytz.UTC)

        # No attempts in the query set, so should return None
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(now, query)
        self.assertIs(result, None)

        # Should also return None if no deadline specified
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(None, query)
        self.assertIs(result, None)

        # Make an attempt
        attempt = SoftwareSecurePhotoVerification.objects.create(user=user)

        # Before the created date, should get no results
        before = attempt.created_at - timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(before, query)
        self.assertIs(result, None)

        # Immediately after the created date, should get the attempt
        after_created = attempt.created_at + timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(after_created, query)
        self.assertEqual(result, attempt)

        # If no deadline specified, should return first available
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(None, query)
        self.assertEqual(result, attempt)

        # Immediately before the expiration date, should get the attempt
        expiration = attempt.created_at + timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
        before_expiration = expiration - timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(before_expiration, query)
        self.assertEqual(result, attempt)

        # Immediately after the expiration date, should not get the attempt
        attempt.created_at = attempt.created_at - timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
        attempt.save()
        after = datetime.now(pytz.UTC) + timedelta(days=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(after, query)
        self.assertIs(result, None)

        # Create a second attempt in the same window
        second_attempt = SoftwareSecurePhotoVerification.objects.create(user=user)

        # Now we should get the newer attempt
        deadline = second_attempt.created_at + timedelta(days=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = verification_for_datetime(deadline, query)
        self.assertEqual(result, second_attempt)
