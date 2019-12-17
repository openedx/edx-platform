import pytz
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.test import TestCase

from django.test.utils import override_settings

from lms.djangoapps.verify_student.models import ManualVerification
from student.tests.factories import UserFactory


class VerifyAllUsersCommandTest(TestCase):
    def test_users_are_verified(self):
        """
        Test that all existing users are verified when the command is run
        """
        users = [UserFactory() for _ in range(3)]

        pre_command_verifications_count = ManualVerification.objects.all().count()
        self.assertEqual(pre_command_verifications_count, 0)

        call_command('verify_all_users')

        post_command_verifications_count = ManualVerification.objects.all().count()
        self.assertEqual(post_command_verifications_count, 3)

    def test_already_verified_users_are_not_verified_again(self):
        """
        Test that already verified users are not verified again when the command is run
        """

        users = [UserFactory() for _ in range(3)]
        for user in users:
            ManualVerification.objects.create(
                user=user,
                reason='SKIP_IDENTITY_VERIFICATION_FOR_TEST',
                status='approved'
            )

        pre_command_verifications_count = ManualVerification.objects.all().count()
        self.assertEqual(pre_command_verifications_count, 3)

        call_command('verify_all_users')

        post_command_verifications_count = ManualVerification.objects.all().count()
        self.assertEqual(post_command_verifications_count, 3)
