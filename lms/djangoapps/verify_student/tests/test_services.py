# -*- coding: utf-8 -*-
"""
Tests for the service classes in verify_student.
"""

from datetime import timedelta

import ddt
from django.conf import settings
from mock import patch
from nose.tools import (
    assert_equals,
    assert_false,
    assert_is_none,
    assert_true
)

from common.test.utils import MockS3Mixin
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from lms.djangoapps.verify_student.services import IDVerificationService
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

FAKE_SETTINGS = {
    "DAYS_GOOD_FOR": 10,
}


@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@ddt.ddt
class TestIDVerificationService(MockS3Mixin, ModuleStoreTestCase):
    """
    Tests for IDVerificationService.
    """

    def test_active_for_user(self):
        """
        Make sure we can retrive a user's active (in progress) verification
        attempt.
        """
        user = UserFactory.create()

        # This user has no active at the moment...
        assert_is_none(IDVerificationService.active_for_user(user))

        # Create an attempt and mark it ready...
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.mark_ready()
        assert_equals(attempt, IDVerificationService.active_for_user(user))

        # A new user won't see this...
        user2 = UserFactory.create()
        user2.save()
        assert_is_none(IDVerificationService.active_for_user(user2))

        # If it's got a different status, it doesn't count
        for status in ["submitted", "must_retry", "approved", "denied"]:
            attempt.status = status
            attempt.save()
            assert_is_none(IDVerificationService.active_for_user(user))

        # But if we create yet another one and mark it ready, it passes again.
        attempt_2 = SoftwareSecurePhotoVerification(user=user)
        attempt_2.mark_ready()
        assert_equals(attempt_2, IDVerificationService.active_for_user(user))

        # And if we add yet another one with a later created time, we get that
        # one instead. We always want the most recent attempt marked ready()
        attempt_3 = SoftwareSecurePhotoVerification(
            user=user,
            created_at=attempt_2.created_at + timedelta(days=1)
        )
        attempt_3.save()

        # We haven't marked attempt_3 ready yet, so attempt_2 still wins
        assert_equals(attempt_2, IDVerificationService.active_for_user(user))

        # Now we mark attempt_3 ready and expect it to come back
        attempt_3.mark_ready()
        assert_equals(attempt_3, IDVerificationService.active_for_user(user))

    def test_user_is_verified(self):
        """
        Test to make sure we correctly answer whether a user has been verified.
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.save()

        # If it's any of these, they're not verified...
        for status in ["created", "ready", "denied", "submitted", "must_retry"]:
            attempt.status = status
            attempt.save()
            assert_false(IDVerificationService.user_is_verified(user), status)

        attempt.status = "approved"
        attempt.save()
        assert_true(IDVerificationService.user_is_verified(user), attempt.status)

    def test_user_has_valid_or_pending(self):
        """
        Determine whether we have to prompt this user to verify, or if they've
        already at least initiated a verification submission.
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)

        # If it's any of these statuses, they don't have anything outstanding
        for status in ["created", "ready", "denied"]:
            attempt.status = status
            attempt.save()
            assert_false(IDVerificationService.user_has_valid_or_pending(user), status)

        # Any of these, and we are. Note the benefit of the doubt we're giving
        # -- must_retry, and submitted both count until we hear otherwise
        for status in ["submitted", "must_retry", "approved"]:
            attempt.status = status
            attempt.save()
            assert_true(IDVerificationService.user_has_valid_or_pending(user), status)

    def test_user_status(self):
        # test for correct status when no error returned
        user = UserFactory.create()
        status = IDVerificationService.user_status(user)
        self.assertEquals(status, ('none', ''))

        # test for when one has been created
        attempt = SoftwareSecurePhotoVerification.objects.create(user=user, status='approved')
        status = IDVerificationService.user_status(user)
        self.assertEquals(status, ('approved', ''))

        # create another one for the same user, make sure the right one is
        # returned
        SoftwareSecurePhotoVerification.objects.create(
            user=user, status='denied', error_msg='[{"photoIdReasons": ["Not provided"]}]'
        )
        status = IDVerificationService.user_status(user)
        self.assertEquals(status, ('approved', ''))

        # now delete the first one and verify that the denial is being handled
        # properly
        attempt.delete()
        status = IDVerificationService.user_status(user)
        self.assertEquals(status, ('must_reverify', ['id_image_missing']))

    @ddt.unpack
    @ddt.data(
        {'enrollment_mode': 'honor', 'status': None, 'output': 'N/A'},
        {'enrollment_mode': 'audit', 'status': None, 'output': 'N/A'},
        {'enrollment_mode': 'verified', 'status': False, 'output': 'Not ID Verified'},
        {'enrollment_mode': 'verified', 'status': True, 'output': 'ID Verified'},
    )
    def test_verification_status_for_user(self, enrollment_mode, status, output):
        """
        Verify verification_status_for_user returns correct status.
        """
        user = UserFactory.create()
        CourseFactory.create()

        with patch(
            'lms.djangoapps.verify_student.services.IDVerificationService.user_is_verified'
        ) as mock_verification:

            mock_verification.return_value = status

            status = IDVerificationService.verification_status_for_user(user, enrollment_mode)
            self.assertEqual(status, output)
