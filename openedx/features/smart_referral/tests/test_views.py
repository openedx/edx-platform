import mock
from ddt import data, ddt
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from rest_framework.test import APITestCase

from lms.djangoapps.onboarding.tests.factories import UserFactory

from .factories import SmartReferralFactory


@ddt
class SmartReferralInvitationAPIViewTest(APITestCase):

    def setUp(self):
        super(SmartReferralInvitationAPIViewTest, self).setUp()
        self.user = UserFactory()
        self.user.set_password('password')
        self.user.save()
        self.client.login(username=self.user.username, password='password')

    @mock.patch('openedx.features.smart_referral.views.task_referral_and_toolkit_emails')
    def test_send_initial_emails_success(self, mock_task_referral_and_toolkit_emails):
        """Successfully send referral emails to two users and current user himself will receive a toolkit email"""

        data = """[
            {"fist_name": "Test1", "last_name": "Referral", "contact_email": "test.referral1@example.com"},
            {"fist_name": "Test2", "last_name": "SmartReferral", "contact_email": "test.referral2@example.com"}
        ]"""
        response = self.client.post(reverse('initial_referral_emails'), data=data, content_type='application/json')

        contact_emails = ['test.referral1@example.com', 'test.referral2@example.com']
        mock_task_referral_and_toolkit_emails.assert_called_once_with(contact_emails, self.user.email)
        self.assertEqual(response.status_code, HTTP_200_OK)

    @mock.patch('openedx.features.smart_referral.views.task_referral_and_toolkit_emails')
    @data('This is invalid json', 'asdasds', None, '', [], {})
    def test_send_initial_emails_invalid_request_data_json(self, data, mock_task_referral_and_toolkit_emails):
        """Submit smart referral invitation request with invalid json"""

        response = self.client.post(reverse('initial_referral_emails'), data=data, content_type='application/json')

        assert not mock_task_referral_and_toolkit_emails.called
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @mock.patch('openedx.features.smart_referral.views.task_referral_and_toolkit_emails')
    def test_send_initial_emails_refer_particular_user_only_once(self, mock_task_referral_and_toolkit_emails):
        """Submit smart referral invitation request and assert that user can refer other, particular, user only once"""

        SmartReferralFactory(user=self.user, contact_email='test.referral@example.com')

        data = '[{"fist_name": "Test", "last_name": "Referral", "contact_email": "test.referral@example.com"}]'
        response = self.client.post(reverse('initial_referral_emails'), data=data, content_type='application/json')

        assert not mock_task_referral_and_toolkit_emails.called
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    @mock.patch('webpack_loader.loader.WebpackLoader.get_bundle')
    @mock.patch('openedx.features.smart_referral.views.task_referral_and_toolkit_emails')
    def test_send_initial_emails_login_required(self, mock_task_referral_and_toolkit_emails, mock_get_bundle):
        """Submit smart referral invitation request without authentication"""

        self.client.logout()

        data = '[{"fist_name": "Test", "last_name": "Referral", "contact_email": "test.referral@example.com"}]'
        response = self.client.post(reverse('initial_referral_emails'), data=data, content_type='application/json')

        assert not mock_task_referral_and_toolkit_emails.called
        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
