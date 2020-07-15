from __future__ import unicode_literals

from datetime import timedelta

import mock
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.features.smart_referral.models import SmartReferral
from openedx.features.smart_referral.tests.factories import SmartReferralFactory
from philu_commands.management.commands.send_referral_follow_up_email import DAYS_TO_SEND_FOLLOW_UP_EMAIL

FIVE_DAYS_TO_SEND_FOLLOW_UP_EMAIL = 5


class SendReferralFollowUpEmails(TestCase):
    """
        Tests for `send_referral_follow_up_email` command.
    """

    @mock.patch('philu_commands.management.commands.send_referral_follow_up_email.task_send_referral_follow_up_emails')
    def test_send_referral_follow_up_emails_command(self, mock_task_send_referral_follow_up_email):
        """
        This test verifies that a call is made to the function 'task_send_referral_follow_up_email' with a list of
        email address. The email address will follow certain criteria. We are getting emails from 'SmartReferral'
        tables so only those entries will be picked that are at-least three days old. If an email address is registered
        on our platform(philu) it will be ignored. Lastly if the 'is_referral_step_complete' flag is 'True' that email
        will also be ignored.
        """

        test_email1 = 'test.referral1@example.com'
        test_email2 = 'test.referral2@example.com'
        test_email3 = 'test.referral3@example.com'
        test_email4 = 'test.referral4@example.com'
        test_email5 = 'test.referral5@example.com'

        today_date = timezone.now()
        three_days_old_date = today_date.date() - timedelta(days=DAYS_TO_SEND_FOLLOW_UP_EMAIL)
        five_days_old_date = today_date.date() - timedelta(days=FIVE_DAYS_TO_SEND_FOLLOW_UP_EMAIL)

        # This email will be ignored as this is today's entry
        SmartReferralFactory(contact_email=test_email1, is_referral_step_complete=False, created=today_date)

        UserFactory(email=test_email2)
        # This entry is three days old and 'is_referral_step_complete' is 'False' but user is registered on our
        # platform so this will be ignored but flag will be updated
        SmartReferralFactory(contact_email=test_email2, is_referral_step_complete=False,
                             created=three_days_old_date)

        # This entry is three days old and 'is_referral_step_complete' is 'True' so this will be ignored
        SmartReferralFactory(contact_email=test_email3, is_referral_step_complete=True,
                             created=three_days_old_date)

        # This entry is three days old and 'is_referral_step_complete' is 'False' and user isn't registered on our
        # platform so this email will be returned in list.
        SmartReferralFactory(contact_email=test_email4, is_referral_step_complete=False,
                             created=three_days_old_date)

        # This entry is five days old and 'is_referral_step_complete' is 'False' and user isn't registered on our
        # platform so this email will be returned in list.
        SmartReferralFactory(contact_email=test_email5, is_referral_step_complete=False,
                             created=five_days_old_date)

        expected_call_arguments = [test_email4, test_email5]
        call_command('send_referral_follow_up_email')

        mock_task_send_referral_follow_up_email.assert_called_once_with(expected_call_arguments)

        test_email2_referral = SmartReferral.objects.filter(contact_email=test_email2).first()
        self.assertTrue(test_email2_referral.is_referral_step_complete)
