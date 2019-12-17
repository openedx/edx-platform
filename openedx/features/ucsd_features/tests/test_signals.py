import pytz
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from django.test.utils import override_settings

from lms.djangoapps.verify_student.models import ManualVerification
from student.tests.factories import UserFactory


class UCSDFeaturesSignalsTests(TestCase):
    def test_user_is_verified_after_creation_when_flag_is_set(self):
        features = settings.FEATURES.copy()
        features['AUTOMATIC_PERMANENT_ACCOUNT_VERIFICATION'] = True
        with override_settings(FEATURES=features):
            user = UserFactory()
            verification_attempt = ManualVerification.objects.get(user=user)
            self.assertTrue(verification_attempt)
            self.assertEqual(verification_attempt.status, 'approved')

    def test_user_is_not_verified_after_creation_when_flag_is_unset(self):
        features = settings.FEATURES.copy()
        features['AUTOMATIC_PERMANENT_ACCOUNT_VERIFICATION'] = False
        with override_settings(FEATURES=features):
            user = UserFactory()
            with self.assertRaises(ObjectDoesNotExist):
                verification_attempt = ManualVerification.objects.get(user=user)

    def test_verification_attempt_expiration_datetime(self):
        features = settings.FEATURES.copy()
        features['AUTOMATIC_PERMANENT_ACCOUNT_VERIFICATION'] = True
        with override_settings(FEATURES=features):
            user = UserFactory()
            verification_attempt = ManualVerification.objects.get(user=user)
            expected_expiration_datetime = datetime.max.replace(tzinfo=pytz.UTC)
            self.assertEqual(verification_attempt.expiration_datetime, expected_expiration_datetime)
