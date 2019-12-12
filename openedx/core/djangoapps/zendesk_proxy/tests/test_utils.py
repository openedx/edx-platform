import ddt
from mock import MagicMock, patch

from django.conf import settings
from django.test.utils import override_settings
from rest_framework import status

from openedx.core.djangoapps.zendesk_proxy.utils import create_zendesk_ticket
from openedx.core.lib.api.test_utils import ApiTestCase


@ddt.ddt
@override_settings(
    ZENDESK_URL="https://www.superrealurlsthataredefinitelynotfake.com",
    ZENDESK_OAUTH_ACCESS_TOKEN="abcdefghijklmnopqrstuvwxyz1234567890"
)
class TestUtils(ApiTestCase):
    def setUp(self):
        self.request_data = {
            'email': 'JohnQStudent@example.com',
            'name': 'John Q. Student',
            'subject': 'Python Unit Test Help Request',
            'body': "Help! I'm trapped in a unit test factory and I can't get out!",
        }
        return super(TestUtils, self).setUp()

    @override_settings(
        ZENDESK_URL=None,
        ZENDESK_OAUTH_ACCESS_TOKEN=None
    )
    def test_missing_settings(self):
        status_code = create_zendesk_ticket(
            requester_name=self.request_data['name'],
            requester_email=self.request_data['email'],
            subject=self.request_data['subject'],
            body=self.request_data['body'],
        )

        self.assertEqual(status_code, 503)

    @ddt.data(201, 400, 401, 403, 404, 500)
    def test_zendesk_status_codes(self, mock_code):
        with patch('requests.post', return_value=MagicMock(status_code=mock_code)):
            status_code = create_zendesk_ticket(
                requester_name=self.request_data['name'],
                requester_email=self.request_data['email'],
                subject=self.request_data['subject'],
                body=self.request_data['body'],
            )

            self.assertEqual(status_code, mock_code)

    def test_unexpected_error_pinging_zendesk(self):
        with patch('requests.post', side_effect=Exception("WHAMMY")):
            status_code = create_zendesk_ticket(
                requester_name=self.request_data['name'],
                requester_email=self.request_data['email'],
                subject=self.request_data['subject'],
                body=self.request_data['body'],
            )
            self.assertEqual(status_code, 500)

    @patch('openedx.core.djangoapps.zendesk_proxy.utils.send_notification_email_to_support', return_value=True)
    def test_send_email_instead_zendesk_ticket_successfully(self, mocked_send_notification):
        """
        Test that email is sent for notification instead of creating a ticket on zendesk when
        `ENABLE_EMAIL_INSTEAD_ZENDESK` feature flag is set to `True`. If email is send successfully
        return 201 status code.
        """
        notification_message_type = 'contact_support'

        features = settings.FEATURES.copy()
        features['ENABLE_EMAIL_INSTEAD_ZENDESK'] = True

        with override_settings(FEATURES=features):
            return_value = create_zendesk_ticket(
                requester_name=self.request_data['name'],
                requester_email=self.request_data['email'],
                subject=self.request_data['subject'],
                body=self.request_data['body'],
            )

            self.assertTrue(mocked_send_notification.called)
            self.assertEqual(
                mocked_send_notification.call_args[1]['message_type'],
                notification_message_type
            )
            self.assertEqual(return_value, status.HTTP_201_CREATED)

    @patch('openedx.core.djangoapps.zendesk_proxy.utils.send_notification_email_to_support', return_value=False)
    def test_send_email_instead_zendesk_ticket_failed(self, mocked_send_notification):
        """
        Test that email is sent for notification instead of creating a ticket on zendesk when
        `ENABLE_EMAIL_INSTEAD_ZENDESK` feature flag is set to `True`. If email is not sent successfully,
        return 503 status code.
        """
        notification_message_type = 'contact_support'

        features = settings.FEATURES.copy()
        features['ENABLE_EMAIL_INSTEAD_ZENDESK'] = True

        with override_settings(FEATURES=features):
            return_value = create_zendesk_ticket(
                requester_name=self.request_data['name'],
                requester_email=self.request_data['email'],
                subject=self.request_data['subject'],
                body=self.request_data['body'],
            )

            self.assertTrue(mocked_send_notification.called)
            self.assertEqual(
                mocked_send_notification.call_args[1]['message_type'],
                notification_message_type
            )
            self.assertEqual(return_value, status.HTTP_503_SERVICE_UNAVAILABLE)
