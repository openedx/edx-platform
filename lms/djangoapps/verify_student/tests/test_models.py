# -*- coding: utf-8 -*-
from __future__ import absolute_import

import base64
import simplejson as json
from datetime import datetime, timedelta

import boto
import ddt
import mock
import requests.exceptions
from django.conf import settings
from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time
from mock import patch
from six.moves import range
from student.tests.factories import UserFactory
from testfixtures import LogCapture
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from common.test.utils import MockS3Mixin
from lms.djangoapps.verify_student.models import (
    SoftwareSecurePhotoVerification,
    SSOVerification,
    ManualVerification,
    VerificationException,
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
        assert data_dict.get(key)

    # The keys should be stored as Base64 strings, i.e. this should not explode
    data_dict["PhotoIDKey"] = base64.b64decode(data_dict["PhotoIDKey"])
    data_dict["UserPhotoKey"] = base64.b64decode(data_dict["UserPhotoKey"])

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


class TestVerification(TestCase):
    """
    Common tests across all types of Verications (e.g., SoftwareSecurePhotoVerication, SSOVerification)
    """

    def verification_active_at_datetime(self, attempt):
        """
        Tests to ensure the Verification is active or inactive at the appropriate datetimes.
        """
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
        attempt.created_at = attempt.created_at - timedelta(days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"])
        attempt.save()
        self.assertFalse(attempt.active_at_datetime(now() + timedelta(days=1)))


# Lots of patching to stub in our own settings, and HTTP posting
@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
@ddt.ddt
class TestPhotoVerification(TestVerification, MockS3Mixin, ModuleStoreTestCase):

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
        self.assertEqual(attempt.status, "created")

        # These should all fail because we're in the wrong starting state.
        self.assertRaises(VerificationException, attempt.submit)
        self.assertRaises(VerificationException, attempt.approve)
        self.assertRaises(VerificationException, attempt.deny)

        # Now let's fill in some values so that we can pass the mark_ready() call
        attempt.mark_ready()
        self.assertEqual(attempt.status, "ready")

        # ready (can't approve or deny unless it's "submitted")
        self.assertRaises(VerificationException, attempt.approve)
        self.assertRaises(VerificationException, attempt.deny)

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
        self.assertRaises(VerificationException, attempt.submit)
        attempt.approve()  # no-op
        attempt.system_error("System error")  # no-op, something processed it without error
        attempt.deny(DENY_ERROR_MSG)

        # denied
        self.assertRaises(VerificationException, attempt.submit)
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

        self.assertEqual(u"Clyde \u01B4", attempt.name)

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
        self.assertEqual(attempt.status, "submitted")

        # We post, but Software Secure doesn't like what we send for some reason
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_error):
            attempt = self.create_and_submit()
            self.assertEqual(attempt.status, "must_retry")

        # We try to post, but run into an error (in this case a network connection error)
        with patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post_unavailable):
            with LogCapture('lms.djangoapps.verify_student.models') as logger:
                attempt = self.create_and_submit()
                self.assertEqual(attempt.status, "must_retry")
                logger.check(
                    ('lms.djangoapps.verify_student.models', 'ERROR',
                     u'Software Secure submission failed for user %s, setting status to must_retry'
                     % attempt.user.username))

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

    # pylint: disable=line-too-long
    def test_parse_error_msg_success(self):
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)
        attempt.status = 'denied'
        attempt.error_msg = '[{"userPhotoReasons": ["Face out of view"]}, {"photoIdReasons": ["Photo hidden/No photo", "ID name not provided"]}]'
        parsed_error_msg = attempt.parsed_error_msg()
        self.assertEqual(
            sorted(parsed_error_msg),
            sorted(['id_image_missing_name', 'user_image_not_clear', 'id_image_not_clear'])
        )

    @ddt.data(
        'Not Provided',
        '{"IdReasons": ["Not provided"]}',
        u'[{"ïḋṚëäṡöṅṡ": ["Ⓝⓞⓣ ⓟⓡⓞⓥⓘⓓⓔⓓ "]}]',
    )
    def test_parse_error_msg_failure(self, msg):
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification.objects.create(user=user, status='denied', error_msg=msg)
        self.assertEqual(attempt.parsed_error_msg(), [])

    def test_active_at_datetime(self):
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification.objects.create(user=user)
        self.verification_active_at_datetime(attempt)

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
        expired_future = now() + timedelta(days=(FAKE_SETTINGS['DAYS_GOOD_FOR'] + 1))
        with freeze_time(expired_future):
            third_result = SoftwareSecurePhotoVerification.get_initial_verification(user)
            self.assertIsNone(third_result)

        # Test method 'get_initial_verification' returns correct attempt after system expiration,
        # but within earliest allowed override.
        expired_future = now() + timedelta(days=(FAKE_SETTINGS['DAYS_GOOD_FOR'] + 1))
        earliest_allowed = now() - timedelta(days=1)
        with freeze_time(expired_future):
            fourth_result = SoftwareSecurePhotoVerification.get_initial_verification(user, earliest_allowed)
            self.assertIsNotNone(fourth_result)
            self.assertEqual(fourth_result, first_result)

    def test_retire_user(self):
        """
        Retire user with record(s) in table
        """
        user = UserFactory.create()
        user.profile.name = u"Enrique"
        attempt = SoftwareSecurePhotoVerification(user=user)

        # Populate Record
        attempt.mark_ready()
        attempt.status = "submitted"
        attempt.photo_id_image_url = "https://example.com/test/image/img.jpg"
        attempt.face_image_url = "https://example.com/test/face/img.jpg"
        attempt.photo_id_key = 'there_was_an_attempt'
        attempt.approve()

        # Validate data before retirement
        self.assertEqual(attempt.name, user.profile.name)
        self.assertEqual(attempt.photo_id_image_url, 'https://example.com/test/image/img.jpg')
        self.assertEqual(attempt.face_image_url, 'https://example.com/test/face/img.jpg')
        self.assertEqual(attempt.photo_id_key, 'there_was_an_attempt')

        # Retire User
        attempt_again = SoftwareSecurePhotoVerification(user=user)
        self.assertTrue(attempt_again.retire_user(user_id=user.id))

        # Validate data after retirement
        self.assertEqual(attempt_again.name, '')
        self.assertEqual(attempt_again.face_image_url, '')
        self.assertEqual(attempt_again.photo_id_image_url, '')
        self.assertEqual(attempt_again.photo_id_key, '')

    def test_retire_nonuser(self):
        """
        Attempt to Retire User with no records in table
        """
        user = UserFactory.create()
        attempt = SoftwareSecurePhotoVerification(user=user)

        # User with no records in table
        self.assertFalse(attempt.retire_user(user_id=user.id))

        # No user
        self.assertFalse(attempt.retire_user(user_id=47))

    def test_get_recent_verification(self):
        """Test that method 'get_recent_verification' of model
        'SoftwareSecurePhotoVerification' always returns the most
        recent 'approved' verification based on updated_at set
        against a user.
        """
        user = UserFactory.create()
        attempt = None

        for _ in range(2):
            # Make an approved verification
            attempt = SoftwareSecurePhotoVerification(user=user)
            attempt.status = 'approved'
            attempt.expiry_date = datetime.now()
            attempt.save()

        # Test method 'get_recent_verification' returns the most recent
        # verification attempt based on updated_at
        recent_verification = SoftwareSecurePhotoVerification.get_recent_verification(user=user)
        self.assertIsNotNone(recent_verification)
        self.assertEqual(recent_verification.id, attempt.id)

    def test_get_recent_verification_expiry_null(self):
        """Test that method 'get_recent_verification' of model
        'SoftwareSecurePhotoVerification' will return None when expiry_date
        is NULL for 'approved' verifications based on updated_at value.
        """
        user = UserFactory.create()
        attempt = None

        for _ in range(2):
            # Make an approved verification
            attempt = SoftwareSecurePhotoVerification(user=user)
            attempt.status = 'approved'
            attempt.save()

        # Test method 'get_recent_verification' returns None
        # as attempts don't have an expiry_date
        recent_verification = SoftwareSecurePhotoVerification.get_recent_verification(user=user)
        self.assertIsNone(recent_verification)

    def test_no_approved_verification(self):
        """Test that method 'get_recent_verification' of model
        'SoftwareSecurePhotoVerification' returns None if no
        'approved' verification are found
        """
        user = UserFactory.create()
        SoftwareSecurePhotoVerification(user=user)

        result = SoftwareSecurePhotoVerification.get_recent_verification(user=user)
        self.assertIs(result, None)

    def test_update_expiry_email_date_for_user(self):
        """Test that method update_expiry_email_date_for_user of
        model 'SoftwareSecurePhotoVerification' set expiry_email_date
        if the most recent approved verification is expired.
        """
        email_config = getattr(settings, 'VERIFICATION_EXPIRY_EMAIL', {'DAYS_RANGE': 1, 'RESEND_DAYS': 15})
        user = UserFactory.create()
        verification = SoftwareSecurePhotoVerification(user=user)
        verification.expiry_date = now() - timedelta(days=FAKE_SETTINGS['DAYS_GOOD_FOR'])
        verification.status = 'approved'
        verification.save()

        self.assertIsNone(verification.expiry_email_date)

        SoftwareSecurePhotoVerification.update_expiry_email_date_for_user(user, email_config)
        result = SoftwareSecurePhotoVerification.get_recent_verification(user=user)

        self.assertIsNotNone(result.expiry_email_date)


class SSOVerificationTest(TestVerification):
    """
    Tests for the SSOVerification model
    """

    def test_active_at_datetime(self):
        user = UserFactory.create()
        attempt = SSOVerification.objects.create(user=user)
        self.verification_active_at_datetime(attempt)


class ManualVerificationTest(TestVerification):
    """
    Tests for the ManualVerification model
    """

    def test_active_at_datetime(self):
        user = UserFactory.create()
        verification = ManualVerification.objects.create(user=user)
        self.verification_active_at_datetime(verification)
