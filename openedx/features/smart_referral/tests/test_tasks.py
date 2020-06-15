import mock
from django.conf import settings
from django.test import TestCase

from common.lib.mandrill_client.client import MandrillClient

from openedx.features.smart_referral.tasks import task_send_referral_and_toolkit_emails


class SmartReferralTasksTest(TestCase):

    @mock.patch('openedx.features.smart_referral.tasks.MandrillClient.send_mail')
    def task_send_referral_and_toolkit_emails_successfully(self, mock_send_mail):
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
