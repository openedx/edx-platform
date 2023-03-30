"""
Tests for django admin command `trigger_softwaresecurephotoverifications_post_save_signal`
in the verify_student module
"""


from django.conf import settings
from django.core.management import call_command

from freezegun import freeze_time
from unittest.mock import call, patch, ANY  # lint-amnesty, pylint: disable=wrong-import-order

from common.test.utils import MockS3Boto3Mixin
from lms.djangoapps.verify_student.tests import TestVerificationBase
from lms.djangoapps.verify_student.tests.test_models import (
    FAKE_SETTINGS,
    mock_software_secure_post,
)


# Lots of patching to stub in our own settings, and HTTP posting
@patch.dict(settings.VERIFY_STUDENT, FAKE_SETTINGS)
@patch.dict(settings.FEATURES, {'AUTOMATIC_VERIFY_STUDENT_IDENTITY_FOR_TESTING': True})
@patch('lms.djangoapps.verify_student.models.requests.post', new=mock_software_secure_post)
class TestTriggerSoftwareSecurePhotoVerificationsPostSaveSignal(MockS3Boto3Mixin, TestVerificationBase):
    """
    Tests for django admin command `trigger_softwaresecurephotoverifications_post_save_signal`
    in the verify_student module
    """

    def setUp(self):
        super().setUp()
        # Test that the correct attempts within a date range are called
        with freeze_time("2023-02-28 23:59:59"):
            self._create_attempts(1)
        with freeze_time("2023-03-01 00:00:00"):
            self._create_attempts(4)
        with freeze_time("2023-03-28 23:59:59"):
            self._create_attempts(4)
        with freeze_time("2023-03-29 00:00:00"):
            self._create_attempts(1)

    def _create_attempts(self, num_attempts):
        for _ in range(num_attempts):
            self.create_and_submit_attempt_for_user()

    @patch('lms.djangoapps.verify_student.signals.idv_update_signal.send')
    def test_command(self, send_idv_update_mock):

        call_command('trigger_softwaresecurephotoverifications_post_save_signal',
                     'submitted',
                     start_datetime="2023-03-01 00:00:00",
                     end_datetime="2023-03-28 23:59:59"
                     )

        # The UserFactory instantiates first_name and last_name using a Sequence, which provide integers to
        # generate unique values. A Sequence maintains its state across test runs, so the value of a given Sequence,
        # and therefore, the value of photo_id_name and full_name, depends on the order that tests using the UserFactory
        # run, as the Sequence is not reset after each test suite. This makes asserting on the exact value
        # of photo_id_name and full_name, derived from first_name and last_name, difficult.
        # Resetting the Sequence with UserFactory.reset_sequence causes failures in other tests that rely on
        # these values. In any case, we primarily care about the signal being called with the correct sender,
        # attempt_id, and user_id, as the signal is tested elsewhere.
        expected_calls = [
            call(
                sender='idv_update', attempt_id=2, user_id=2, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=3, user_id=3, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=4, user_id=4, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=5, user_id=5, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=6, user_id=6, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=7, user_id=7, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=8, user_id=8, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
            call(
                sender='idv_update', attempt_id=9, user_id=9, status='submitted',
                photo_id_name=ANY, full_name=ANY
            ),
        ]
        print(send_idv_update_mock.mock_calls)
        self.assertEqual(send_idv_update_mock.call_count, 8)
        send_idv_update_mock.assert_has_calls(expected_calls, any_order=True)
