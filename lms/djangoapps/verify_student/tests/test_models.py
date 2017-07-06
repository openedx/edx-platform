# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
import json

import boto
import ddt
from django.conf import settings
from django.db import IntegrityError
from django.test import TestCase
from freezegun import freeze_time
import mock
from mock import patch
from nose.tools import assert_is_none, assert_equals, assert_raises, assert_true, assert_false  # pylint: disable=no-name-in-module
import pytz
import requests.exceptions

from common.test.utils import MockS3Mixin
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase

from lms.djangoapps.verify_student.models import (
    SoftwareSecurePhotoVerification,
    VerificationException, VerificationCheckpoint,
    VerificationStatus, SkippedReverification,
    VerificationDeadline
)

FAKE_SETTINGS = {
    "SOFTWARE_SECURE": {
        "FACE_IMAGE_AES_KEY": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        "API_ACCESS_KEY": "BBBBBBBBBBBBBBBBBBBB",
        "API_SECRET_KEY": "CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
        "RSA_PUBLIC_KEY": """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu2fUn20ZQtDpa1TKeCA/
rDA2cEeFARjEr41AP6jqP/k3O7TeqFX6DgCBkxcjojRCs5IfE8TimBHtv/bcSx9o
7PANTq/62ZLM9xAMpfCcU6aAd4+CVqQkXSYjj5TUqamzDFBkp67US8IPmw7I2Gaa
tX8ErZ9D7ieOJ8/0hEiphHpCZh4TTgGuHgjon6vMV8THtq3AQMaAQ/y5R3V7Lezw
dyZCM9pBcvcH+60ma+nNg8GVGBAW/oLxILBtg+T3PuXSUvcu/r6lUFMHk55pU94d
9A/T8ySJm379qU24ligMEetPk1o9CUasdaI96xfXVDyFhrzrntAmdD+HYCSPOQHz
iwIDAQAB
-----END PUBLIC KEY-----""",
        "API_URL": "http://localhost/verify_student/fake_endpoint",
        "AWS_ACCESS_KEY": "FAKEACCESSKEY",
        "AWS_SECRET_KEY": "FAKESECRETKEY",
        "S3_BUCKET": "fake-bucket",
    },
    "DAYS_GOOD_FOR": 10,
}


def mock_software_secure_post(url, headers=None, data=None, **kwargs):
    """
    Mocks our interface when we post to Software Secure. Does basic assertions
    on the fields we send over to make sure we're not missing headers or giving
    total garbage.
    """
    data_dict = json.loads(data)

    # Basic sanity checking on the keys
    EXPECTED_KEYS = [
        "EdX-ID", "ExpectedName", "PhotoID", "PhotoIDKey", "SendResponseTo",
        "UserPhoto", "UserPhotoKey",
    ]
    for key in EXPECTED_KEYS:
        assert_true(
            data_dict.get(key),
            "'{}' must be present and not blank in JSON submitted to Software Secure".format(key)
        )

    # The keys should be stored as Base64 strings, i.e. this should not explode
    photo_id_key = data_dict["PhotoIDKey"].decode("base64")
    user_photo_key = data_dict["UserPhotoKey"].decode("base64")

    response = requests.Response()
    response.status_code = 200

    return response


def mock_software_secure_post_error(url, headers=None, data=None, **kwargs):
    """
    Simulates what happens if our post to Software Secure is rejected, for
    whatever reason.
    """
    response = requests.Response()
    response.status_code = 400
    return response


def mock_software_secure_post_unavailable(url, headers=None, data=None, **kwargs):
    """Simulates a connection failure when we try to submit to Software Secure."""
    raise requests.exceptions.ConnectionError


# Lots of patching to stub in our own settings, and HTTP posting
@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
@ddt.ddt
class TestPhotoVerification(MockS3Mixin, ModuleStoreTestCase):

    def setUp(self):
        super(TestPhotoVerification, self).setUp()
        connection = boto.connect_s3()
        connection.create_bucket(FAKE_SETTINGS['SOFTWARE_SECURE']['S3_BUCKET'])

    def test_state_transitions(self):
        """
        Make sure we can't make unexpected status transitions.

        The status transitions we expect are::

                        → → → must_retry
                        ↑        ↑ ↓
            created → ready → submitted → approved
                                    ↓        ↑ ↓
                                    ↓ → →  denied
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        assert_equals(attempt.status, "created")

        # These should all fail because we're in the wrong starting state.
        assert_raises(VerificationException, attempt.submit)
        assert_raises(VerificationException, attempt.approve)
        assert_raises(VerificationException, attempt.deny)

        # Now let's fill in some values so that we can pass the mark_ready() call
        attempt.mark_ready()
        assert_equals(attempt.status, "ready")

        # ready (can't approve or deny unless it's "submitted")
        assert_raises(VerificationException, attempt.approve)
        assert_raises(VerificationException, attempt.deny)

        DENY_ERROR_MSG = '[{"photoIdReasons": ["Not provided"]}]'

        # must_retry
        attempt.status = "must_retry"
        attempt.system_error("System error")
        attempt.approve()
        attempt.status = "must_retry"
        attempt.deny(DENY_ERROR_MSG)

        # submitted
        attempt.status = "submitted"
        attempt.deny(DENY_ERROR_MSG)
        attempt.status = "submitted"
        attempt.approve()

        # approved
        assert_raises(VerificationException, attempt.submit)
        attempt.approve()  # no-op
        attempt.system_error("System error")  # no-op, something processed it without error
        attempt.deny(DENY_ERROR_MSG)

        # denied
        assert_raises(VerificationException, attempt.submit)
        attempt.deny(DENY_ERROR_MSG)  # no-op
        attempt.system_error("System error")  # no-op, something processed it without error
        attempt.approve()

    def test_name_freezing(self):
        """
        You can change your name prior to marking a verification attempt ready,
        but changing your name afterwards should not affect the value in the
        in the attempt record. Basically, we want to always know what your name
        was when you submitted it.
        """
        user = UserFactory.create()
        user.profile.name = u"Jack \u01B4"  # gratuious non-ASCII char to test encodings

        attempt = SoftwareSecurePhotoVerification(user=user)
        user.profile.name = u"Clyde \u01B4"
        attempt.mark_ready()

        user.profile.name = u"Rusty \u01B4"

        assert_equals(u"Clyde \u01B4", attempt.name)

    def create_and_submit(self):
        """Helper method to create a generic submission and send it."""
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        user.profile.name = u"Rust\u01B4"

        attempt.upload_face_image("Just pretend this is image data")
        attempt.upload_photo_id_image("Hey, we're a photo ID")
        attempt.mark_ready()
        attempt.submit()

        return attempt

    def test_submissions(self):
        """Test that we set our status correctly after a submission."""
        # Basic case, things go well.
        attempt = self.create_and_submit()
        assert_equals(attempt.status, "submitted")

        # We post, but Software Secure doesn't like what we send for some reason
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_error):
            attempt = self.create_and_submit()
            assert_equals(attempt.status, "must_retry")

        # We try to post, but run into an error (in this case a newtork connection error)
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_unavailable):
            attempt = self.create_and_submit()
            assert_equals(attempt.status, "must_retry")

    @mock.patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
    def test_submission_while_testing_flag_is_true(self):
        """ Test that a fake value is set for field 'photo_id_key' of user's
        initial verification when the feature flag 'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING'
        is enabled.
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        user.profile.name = "test-user"

        attempt.upload_photo_id_image("Image data")
        attempt.mark_ready()
        attempt.submit()

        self.assertEqual(attempt.photo_id_key, "fake-photo-id-key")

    def test_active_for_user(self):
        """
        Make sure we can retrive a user's active (in progress) verification
        attempt.
        """
        user = UserFactory.create()

        # This user has no active at the moment...
        assert_is_none(SoftwareSecurePhotoVerification.active_for_user(user))

        # Create an attempt and mark it ready...
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.mark_ready()
        assert_equals(attempt, SoftwareSecurePhotoVerification.active_for_user(user))

        # A new user won't see this...
        user2 = UserFactory.create()
        user2.save()
        assert_is_none(SoftwareSecurePhotoVerification.active_for_user(user2))

        # If it's got a different status, it doesn't count
        for status in ["submitted", "must_retry", "approved", "denied"]:
            attempt.status = status
            attempt.save()
            assert_is_none(SoftwareSecurePhotoVerification.active_for_user(user))

        # But if we create yet another one and mark it ready, it passes again.
        attempt_2 = SoftwareSecurePhotoVerification(user=user)
        attempt_2.mark_ready()
        assert_equals(attempt_2, SoftwareSecurePhotoVerification.active_for_user(user))

        # And if we add yet another one with a later created time, we get that
        # one instead. We always want the most recent attempt marked ready()
        attempt_3 = SoftwareSecurePhotoVerification(
            user=user,
            created_at=attempt_2.created_at + timedelta(days=1)
        )
        attempt_3.save()

        # We haven't marked attempt_3 ready yet, so attempt_2 still wins
        assert_equals(attempt_2, SoftwareSecurePhotoVerification.active_for_user(user))

        # Now we mark attempt_3 ready and expect it to come back
        attempt_3.mark_ready()
        assert_equals(attempt_3, SoftwareSecurePhotoVerification.active_for_user(user))

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
            assert_false(SoftwareSecurePhotoVerification.user_is_verified(user), status)

        attempt.status = "approved"
        attempt.save()
        assert_true(SoftwareSecurePhotoVerification.user_is_verified(user), attempt.status)

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
            assert_false(SoftwareSecurePhotoVerification.user_has_valid_or_pending(user), status)

        # Any of these, and we are. Note the benefit of the doubt we're giving
        # -- must_retry, and submitted both count until we hear otherwise
        for status in ["submitted", "must_retry", "approved"]:
            attempt.status = status
            attempt.save()
            assert_true(SoftwareSecurePhotoVerification.user_has_valid_or_pending(user), status)

    def test_user_status(self):
        # test for correct status when no error returned
        user = UserFactory.create()
        status = SoftwareSecurePhotoVerification.user_status(user)
        self.assertEquals(status, ('none', ''))

        # test for when one has been created
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.status = 'approved'
        attempt.save()

        status = SoftwareSecurePhotoVerification.user_status(user)
        self.assertEquals(status, ('approved', ''))

        # create another one for the same user, make sure the right one is
        # returned
        attempt2 = SoftwareSecurePhotoVerification(user=user)
        attempt2.status = 'denied'
        attempt2.error_msg = '[{"photoIdReasons": ["Not provided"]}]'
        attempt2.save()

        status = SoftwareSecurePhotoVerification.user_status(user)
        self.assertEquals(status, ('approved', ''))

        # now delete the first one and verify that the denial is being handled
        # properly
        attempt.delete()
        status = SoftwareSecurePhotoVerification.user_status(user)
        self.assertEquals(status, ('must_reverify', "No photo ID was provided."))

    def test_parse_error_msg_success(self):
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.status = 'denied'
        attempt.error_msg = '[{"photoIdReasons": ["Not provided"]}]'
        parsed_error_msg = attempt.parsed_error_msg()
        self.assertEquals("No photo ID was provided.", parsed_error_msg)

    def test_parse_error_msg_failure(self):
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.status = 'denied'
        # when we can't parse into json
        bad_messages = {
            'Not Provided',
            '[{"IdReasons": ["Not provided"]}]',
            '{"IdReasons": ["Not provided"]}',
            u'[{"ïḋṚëäṡöṅṡ": ["Ⓝⓞⓣ ⓟⓡⓞⓥⓘⓓⓔⓓ "]}]',
        }
        for msg in bad_messages:
            attempt.error_msg = msg
            parsed_error_msg = attempt.parsed_error_msg()
            self.assertEquals(parsed_error_msg, "There was an error verifying your ID photos.")

    def test_active_at_datetime(self):
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification.objects.create(user=user)

        # Not active before the created date
        before = attempt.created_at - timedelta(seconds=1)
        self.assertFalse(attempt.active_at_datetime(before))

        # Active immediately after created date
        after_created = attempt.created_at + timedelta(seconds=1)
        self.assertTrue(attempt.active_at_datetime(after_created))

        # Active immediately before expiration date
        expiration = attempt.created_at + timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
        before_expiration = expiration - timedelta(seconds=1)
        self.assertTrue(attempt.active_at_datetime(before_expiration))

        # Not active after the expiration date
        after = expiration + timedelta(seconds=1)
        self.assertFalse(attempt.active_at_datetime(after))

    def test_verification_for_datetime(self):
        user = UserFactory.create()
        now = datetime.now(pytz.UTC)

        # No attempts in the query set, so should return None
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(now, query)
        self.assertIs(result, None)

        # Should also return None if no deadline specified
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(None, query)
        self.assertIs(result, None)

        # Make an attempt
        attempt = SoftwareSecurePhotoVerification.objects.create(user=user)

        # Before the created date, should get no results
        before = attempt.created_at - timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(before, query)
        self.assertIs(result, None)

        # Immediately after the created date, should get the attempt
        after_created = attempt.created_at + timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(after_created, query)
        self.assertEqual(result, attempt)

        # If no deadline specified, should return first available
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(None, query)
        self.assertEqual(result, attempt)

        # Immediately before the expiration date, should get the attempt
        expiration = attempt.created_at + timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
        before_expiration = expiration - timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(before_expiration, query)
        self.assertEqual(result, attempt)

        # Immediately after the expiration date, should not get the attempt
        after = expiration + timedelta(seconds=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(after, query)
        self.assertIs(result, None)

        # Create a second attempt in the same window
        second_attempt = SoftwareSecurePhotoVerification.objects.create(user=user)

        # Now we should get the newer attempt
        deadline = second_attempt.created_at + timedelta(days=1)
        query = SoftwareSecurePhotoVerification.objects.filter(user=user)
        result = SoftwareSecurePhotoVerification.verification_for_datetime(deadline, query)
        self.assertEqual(result, second_attempt)

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
        course = CourseFactory.create()

        with patch(
            'lms.djangoapps.verify_student.models.SoftwareSecurePhotoVerification.user_is_verified'
        ) as mock_verification:

            mock_verification.return_value = status

            status = SoftwareSecurePhotoVerification.verification_status_for_user(user, course.id, enrollment_mode)
            self.assertEqual(status, output)

    def test_initial_verification_for_user(self):
        """Test that method 'get_initial_verification' of model
        'SoftwareSecurePhotoVerification' always returns the initial
        verification with field 'photo_id_key' set against a user.
        """
        user = UserFactory.create()

        # No initial verification for the user
        result = SoftwareSecurePhotoVerification.get_initial_verification(user=user)
        self.assertIs(result, None)

        # Make an initial verification with 'photo_id_key'
        attempt = SoftwareSecurePhotoVerification(user=user, photo_id_key="dummy_photo_id_key")
        attempt.status = 'approved'
        attempt.save()

        # Check that method 'get_initial_verification' returns the correct
        # initial verification attempt
        first_result = SoftwareSecurePhotoVerification.get_initial_verification(user=user)
        self.assertIsNotNone(first_result)

        # Now create a second verification without 'photo_id_key'
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.status = 'submitted'
        attempt.save()

        # Test method 'get_initial_verification' still returns the correct
        # initial verification attempt which have 'photo_id_key' set
        second_result = SoftwareSecurePhotoVerification.get_initial_verification(user=user)
        self.assertIsNotNone(second_result)
        self.assertEqual(second_result, first_result)

        # Test method 'get_initial_verification' returns None after expiration
        expired_future = datetime.utcnow() + timedelta(days=(FAKE_SETTINGS['DAYS_GOOD_FOR'] + 1))
        with freeze_time(expired_future):
            third_result = SoftwareSecurePhotoVerification.get_initial_verification(user)
            self.assertIsNone(third_result)

        # Test method 'get_initial_verification' returns correct attempt after system expiration,
        # but within earliest allowed override.
        expired_future = datetime.utcnow() + timedelta(days=(FAKE_SETTINGS['DAYS_GOOD_FOR'] + 1))
        earliest_allowed = datetime.utcnow() - timedelta(days=1)
        with freeze_time(expired_future):
            fourth_result = SoftwareSecurePhotoVerification.get_initial_verification(user, earliest_allowed)
            self.assertIsNotNone(fourth_result)
            self.assertEqual(fourth_result, first_result)


@ddt.ddt
class VerificationCheckpointTest(ModuleStoreTestCase):
    """Tests for the VerificationCheckpoint model. """

    def setUp(self):
        super(VerificationCheckpointTest, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        self.checkpoint_midterm = u'i4x://{org}/{course}/edx-reverification-block/midterm_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )
        self.checkpoint_final = u'i4x://{org}/{course}/edx-reverification-block/final_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )

    @ddt.data('midterm', 'final')
    def test_get_or_create_verification_checkpoint(self, checkpoint):
        """
        Test that a reverification checkpoint is created properly.
        """
        checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/{checkpoint}'.format(
            org=self.course.id.org, course=self.course.id.course, checkpoint=checkpoint
        )
        # create the 'VerificationCheckpoint' checkpoint
        verification_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=checkpoint_location
        )
        self.assertEqual(
            VerificationCheckpoint.get_or_create_verification_checkpoint(self.course.id, checkpoint_location),
            verification_checkpoint
        )

    def test_get_or_create_verification_checkpoint_for_not_existing_values(self):
        # Retrieving a checkpoint that doesn't yet exist will create it
        location = u'i4x://edX/DemoX/edx-reverification-block/invalid_location'
        checkpoint = VerificationCheckpoint.get_or_create_verification_checkpoint(self.course.id, location)

        self.assertIsNot(checkpoint, None)
        self.assertEqual(checkpoint.course_id, self.course.id)
        self.assertEqual(checkpoint.checkpoint_location, location)

    def test_get_or_create_integrity_error(self):
        # Create the checkpoint
        VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.checkpoint_midterm,
        )

        # Simulate that the get-or-create operation raises an IntegrityError.
        # This can happen when two processes both try to get-or-create at the same time
        # when the database is set to REPEATABLE READ.
        # To avoid IntegrityError situations when calling this method, set the view to
        # use a READ COMMITTED transaction instead.
        with patch.object(VerificationCheckpoint.objects, "get_or_create") as mock_get_or_create:
            mock_get_or_create.side_effect = IntegrityError
            with self.assertRaises(IntegrityError):
                _ = VerificationCheckpoint.get_or_create_verification_checkpoint(
                    self.course.id,
                    self.checkpoint_midterm
                )

    def test_unique_together_constraint(self):
        """
        Test the unique together constraint.
        """
        # create the VerificationCheckpoint checkpoint
        VerificationCheckpoint.objects.create(course_id=self.course.id, checkpoint_location=self.checkpoint_midterm)

        # test creating the VerificationCheckpoint checkpoint with same course
        # id and checkpoint name
        with self.assertRaises(IntegrityError):
            VerificationCheckpoint.objects.create(course_id=self.course.id, checkpoint_location=self.checkpoint_midterm)

    def test_add_verification_attempt_software_secure(self):
        """
        Test adding Software Secure photo verification attempts for the
        reverification checkpoints.
        """
        # adding two check points.
        first_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id, checkpoint_location=self.checkpoint_midterm
        )
        second_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id, checkpoint_location=self.checkpoint_final
        )

        # make an attempt for the 'first_checkpoint'
        first_checkpoint.add_verification_attempt(SoftwareSecurePhotoVerification.objects.create(user=self.user))
        self.assertEqual(first_checkpoint.photo_verification.count(), 1)

        # make another attempt for the 'first_checkpoint'
        first_checkpoint.add_verification_attempt(SoftwareSecurePhotoVerification.objects.create(user=self.user))
        self.assertEqual(first_checkpoint.photo_verification.count(), 2)

        # make new attempt for the 'second_checkpoint'
        attempt = SoftwareSecurePhotoVerification.objects.create(user=self.user)
        second_checkpoint.add_verification_attempt(attempt)
        self.assertEqual(second_checkpoint.photo_verification.count(), 1)

        # remove the attempt from 'second_checkpoint'
        second_checkpoint.photo_verification.remove(attempt)
        self.assertEqual(second_checkpoint.photo_verification.count(), 0)


@ddt.ddt
class VerificationStatusTest(ModuleStoreTestCase):
    """ Tests for the VerificationStatus model. """

    def setUp(self):
        super(VerificationStatusTest, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create()

        self.first_checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/first_checkpoint_uuid'.format(
            org=self.course.id.org, course=self.course.id.course
        )
        self.first_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.first_checkpoint_location
        )

        self.second_checkpoint_location = u'i4x://{org}/{course}/edx-reverification-block/second_checkpoint_uuid'.\
            format(org=self.course.id.org, course=self.course.id.course)
        self.second_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.second_checkpoint_location
        )

    @ddt.data('submitted', "approved", "denied", "error")
    def test_add_verification_status(self, status):
        """ Adding verification status using the class method. """

        # adding verification status
        VerificationStatus.add_verification_status(
            checkpoint=self.first_checkpoint,
            user=self.user,
            status=status
        )

        # test the status from database
        result = VerificationStatus.objects.filter(checkpoint=self.first_checkpoint)[0]
        self.assertEqual(result.status, status)
        self.assertEqual(result.user, self.user)

    @ddt.data("approved", "denied", "error")
    def test_add_status_from_checkpoints(self, status):
        """Test verification status for reverification checkpoints after
        submitting software secure photo verification.
        """

        # add initial verification status for checkpoints
        initial_status = "submitted"
        VerificationStatus.add_verification_status(
            checkpoint=self.first_checkpoint,
            user=self.user,
            status=initial_status
        )
        VerificationStatus.add_verification_status(
            checkpoint=self.second_checkpoint,
            user=self.user,
            status=initial_status
        )

        # now add verification status for multiple checkpoint points
        VerificationStatus.add_status_from_checkpoints(
            checkpoints=[self.first_checkpoint, self.second_checkpoint], user=self.user, status=status
        )

        # test that verification status entries with new status have been added
        # for both checkpoints
        result = VerificationStatus.objects.filter(user=self.user, checkpoint=self.first_checkpoint)
        self.assertEqual(len(result), len(self.first_checkpoint.checkpoint_status.all()))
        self.assertEqual(
            list(result.values_list('checkpoint__checkpoint_location', flat=True)),
            list(self.first_checkpoint.checkpoint_status.values_list('checkpoint__checkpoint_location', flat=True))
        )

        result = VerificationStatus.objects.filter(user=self.user, checkpoint=self.second_checkpoint)
        self.assertEqual(len(result), len(self.second_checkpoint.checkpoint_status.all()))
        self.assertEqual(
            list(result.values_list('checkpoint__checkpoint_location', flat=True)),
            list(self.second_checkpoint.checkpoint_status.values_list('checkpoint__checkpoint_location', flat=True))
        )

    def test_get_location_id(self):
        """
        Getting location id for a specific checkpoint.
        """

        # creating software secure attempt against checkpoint
        self.first_checkpoint.add_verification_attempt(SoftwareSecurePhotoVerification.objects.create(user=self.user))

        # add initial verification status for checkpoint
        VerificationStatus.add_verification_status(
            checkpoint=self.first_checkpoint,
            user=self.user,
            status='submitted',
        )
        attempt = SoftwareSecurePhotoVerification.objects.filter(user=self.user)

        self.assertIsNotNone(VerificationStatus.get_location_id(attempt))
        self.assertEqual(VerificationStatus.get_location_id(None), '')

    def test_get_user_attempts(self):
        """
        Test adding verification status.
        """
        VerificationStatus.add_verification_status(
            checkpoint=self.first_checkpoint,
            user=self.user,
            status='submitted'
        )

        actual_attempts = VerificationStatus.get_user_attempts(
            self.user.id,
            self.course.id,
            self.first_checkpoint_location
        )
        self.assertEqual(actual_attempts, 1)


class SkippedReverificationTest(ModuleStoreTestCase):
    """
    Tests for the SkippedReverification model.
    """

    def setUp(self):
        super(SkippedReverificationTest, self).setUp()
        self.user = UserFactory.create()
        self.course = CourseFactory.create()
        dummy_checkpoint_location = u'i4x://edX/DemoX/edx-reverification-block/midterm_uuid'
        self.checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=dummy_checkpoint_location
        )

    def test_add_skipped_attempts(self):
        """
        Test 'add_skipped_reverification_attempt' method.
        """

        # add verification status
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.checkpoint, user_id=self.user.id, course_id=unicode(self.course.id)
        )

        # test the status of skipped reverification from database
        result = SkippedReverification.objects.filter(course_id=self.course.id)[0]
        self.assertEqual(result.checkpoint, self.checkpoint)
        self.assertEqual(result.user, self.user)
        self.assertEqual(result.course_id, self.course.id)

    def test_unique_constraint(self):
        """Test that adding skipped re-verification with same user and course
        id will raise 'IntegrityError' exception.
        """
        # add verification object
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.checkpoint, user_id=self.user.id, course_id=unicode(self.course.id)
        )
        with self.assertRaises(IntegrityError):
            SkippedReverification.add_skipped_reverification_attempt(
                checkpoint=self.checkpoint, user_id=self.user.id, course_id=unicode(self.course.id)
            )

        # create skipped attempt for different user
        user2 = UserFactory.create()
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.checkpoint, user_id=user2.id, course_id=unicode(self.course.id)
        )

        # test the status of skipped reverification from database
        result = SkippedReverification.objects.filter(user=user2)[0]
        self.assertEqual(result.checkpoint, self.checkpoint)
        self.assertEqual(result.user, user2)
        self.assertEqual(result.course_id, self.course.id)

    def test_check_user_skipped_reverification_exists(self):
        """
        Test the 'check_user_skipped_reverification_exists' method's response.
        """
        # add verification status
        SkippedReverification.add_skipped_reverification_attempt(
            checkpoint=self.checkpoint, user_id=self.user.id, course_id=unicode(self.course.id)
        )
        self.assertTrue(
            SkippedReverification.check_user_skipped_reverification_exists(
                user_id=self.user.id,
                course_id=self.course.id
            )
        )

        user2 = UserFactory.create()
        self.assertFalse(
            SkippedReverification.check_user_skipped_reverification_exists(
                user_id=user2.id,
                course_id=self.course.id
            )
        )


class VerificationDeadlineTest(CacheIsolationTestCase):
    """
    Tests for the VerificationDeadline model.
    """

    ENABLED_CACHES = ['default']

    def test_caching(self):
        deadlines = {
            CourseKey.from_string("edX/DemoX/Fall"): datetime.now(pytz.UTC),
            CourseKey.from_string("edX/DemoX/Spring"): datetime.now(pytz.UTC) + timedelta(days=1)
        }
        course_keys = deadlines.keys()

        # Initially, no deadlines are set
        with self.assertNumQueries(1):
            all_deadlines = VerificationDeadline.deadlines_for_courses(course_keys)
            self.assertEqual(all_deadlines, {})

        # Create the deadlines
        for course_key, deadline in deadlines.iteritems():
            VerificationDeadline.objects.create(
                course_key=course_key,
                deadline=deadline,
            )

        # Warm the cache
        with self.assertNumQueries(1):
            VerificationDeadline.deadlines_for_courses(course_keys)

        # Load the deadlines from the cache
        with self.assertNumQueries(0):
            all_deadlines = VerificationDeadline.deadlines_for_courses(course_keys)
            self.assertEqual(all_deadlines, deadlines)

        # Delete the deadlines
        VerificationDeadline.objects.all().delete()

        # Verify that the deadlines are updated correctly
        with self.assertNumQueries(1):
            all_deadlines = VerificationDeadline.deadlines_for_courses(course_keys)
            self.assertEqual(all_deadlines, {})
