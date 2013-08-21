# -*- coding: utf-8 -*-
from nose.tools import (
    assert_in, assert_is_none, assert_equals, assert_raises, assert_not_equals
)
from django.test import TestCase
from student.tests.factories import UserFactory
from verify_student.models import SoftwareSecurePhotoVerification, VerificationException


class TestPhotoVerification(TestCase):

    def test_state_transitions(self):
        """Make sure we can't make unexpected status transitions.

        The status transitions we expect are::

            created → ready → submitted → approved
                                            ↑ ↓
                                        →  denied
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        assert_equals(attempt.status, SoftwareSecurePhotoVerification.STATUS.created)
        assert_equals(attempt.status, "created")

        # This should fail because we don't have the necessary fields filled out
        assert_raises(VerificationException, attempt.mark_ready)

        # These should all fail because we're in the wrong starting state.
        assert_raises(VerificationException, attempt.submit)
        assert_raises(VerificationException, attempt.approve)
        assert_raises(VerificationException, attempt.deny)

        # Now let's fill in some values so that we can pass the mark_ready() call
        attempt.face_image_url = "http://fake.edx.org/face.jpg"
        attempt.photo_id_image_url = "http://fake.edx.org/photo_id.jpg"
        attempt.mark_ready()
        assert_equals(attempt.name, user.profile.name) # Move this to another test
        assert_equals(attempt.status, "ready")

        # Once again, state transitions should fail here. We can't approve or
        # deny anything until it's been placed into the submitted state -- i.e.
        # the user has clicked on whatever agreements, or given payment, or done
        # whatever the application requires before it agrees to process their
        # attempt.
        assert_raises(VerificationException, attempt.approve)
        assert_raises(VerificationException, attempt.deny)

        # Now we submit
        attempt.submit()
        assert_equals(attempt.status, "submitted")

        # So we should be able to both approve and deny
        attempt.approve()
        assert_equals(attempt.status, "approved")

        attempt.deny("Could not read name on Photo ID")
        assert_equals(attempt.status, "denied")


