import mock
from django.conf import settings
from django.test import TestCase

from common.lib.mandrill_client.client import MandrillClient

from openedx.features.smart_referral.models import SmartReferral
from openedx.features.smart_referral.tasks import (
    task_send_referral_and_toolkit_emails,
    task_send_referral_follow_up_emails
)

from .factories import SmartReferralFactory


class SmartReferralTasksTest(TestCase):

    @mock.patch('openedx.features.smart_referral.tasks.MandrillClient.send_mail')
    def test_task_send_referral_and_toolkit_emails_successfully(self, mock_send_mail):
        test_email1 = 'test.referral1@example.com'
        test_email2 = 'test.referral2@example.com'
        user_email = 'user_email@example.com'

        contact_emails = [test_email1, test_email2]
        task_send_referral_and_toolkit_emails(contact_emails, user_email)

        context = {
            'root_url': settings.LMS_ROOT_URL,
        }
        all_rerun_mock_calls = [
            mock.call(MandrillClient.REFERRAL_INITIAL_EMAIL, test_email1, context=context),
            mock.call(MandrillClient.REFERRAL_INITIAL_EMAIL, test_email2, context=context),
            mock.call(MandrillClient.REFERRAL_SOCIAL_IMPACT_TOOLKIT, user_email, context={})
        ]

        self.assertEqual(mock_send_mail.call_count, 3)
        mock_send_mail.assert_has_calls(all_rerun_mock_calls)

    @mock.patch('openedx.features.smart_referral.tasks.MandrillClient.send_mail')
    def test_task_send_referral_follow_up_emails_successfully(self, mock_send_mail):
        test_email1 = 'test.referral1@example.com'
        test_email2 = 'test.referral2@example.com'

        SmartReferralFactory(contact_email=test_email1, is_referral_step_complete=False)
        SmartReferralFactory(contact_email=test_email2, is_referral_step_complete=False)

        contact_emails = [test_email1, test_email2]

        status_first_referral = [
            {
                'status': 'sent',
                'email': test_email1
            }
        ]

        status_second_referral = [
            {
                'status': 'sent',
                'email': test_email2
            }
        ]

        mock_send_mail.side_effect = (status_first_referral, status_second_referral)
        task_send_referral_follow_up_emails(contact_emails)

        context = {
            'root_url': settings.LMS_ROOT_URL,
        }

        all_rerun_mock_calls = [
            mock.call(MandrillClient.REFERRAL_FOLLOW_UP_EMAIL, test_email1, context=context),
            mock.call(MandrillClient.REFERRAL_FOLLOW_UP_EMAIL, test_email2, context=context)
        ]

        self.assertEqual(mock_send_mail.call_count, 2)
        mock_send_mail.assert_has_calls(all_rerun_mock_calls)

        first_referral = SmartReferral.objects.get(contact_email=test_email1)
        second_referral = SmartReferral.objects.get(contact_email=test_email2)

        self.assertTrue(first_referral.is_referral_step_complete)
        self.assertTrue(second_referral.is_referral_step_complete)
