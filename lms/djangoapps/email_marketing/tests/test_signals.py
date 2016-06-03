"""Tests of email marketing signal handlers."""
import logging

from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
from util.json_request import JsonResponse

from email_marketing.signals import handle_unenroll_done, add_email_marketing_cookies, \
    email_marketing_register_user, email_marketing_user_field_changed
from email_marketing.tasks import update_user, update_user_email
from email_marketing.models import EmailMarketingConfiguration
from django.test.client import RequestFactory
from student.tests.factories import UserFactory, UserProfileFactory

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_response import SailthruResponse
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)


def update_email_marketing_config(enabled=False, key='badkey', secret='badsecret', new_user_list='new list'):
    """
    Enable / Disable Sailthru integration
    """
    EmailMarketingConfiguration.objects.create(
        sailthru_enabled=enabled,
        sailthru_key=key,
        sailthru_secret=secret,
        sailthru_new_user_list=new_user_list
    )


class EmailMarketingTests(TestCase):
    """
    Tests for the EmailMarketing signals and tasks classes.
    """

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = UserFactory.build(username='test', email='test@edx.org')
        self.profile = UserProfileFactory.build(user=self.user)
        self.request = self.request_factory.get("foo")
        update_email_marketing_config(enabled=True)
        super(EmailMarketingTests, self).setUp()

    def test_is_enabled(self):
        """
        Verify that is_enabled() returns True when sailthru integration is enabled.
        """
        is_enabled = EmailMarketingConfiguration.current().sailthru_enabled
        self.assertTrue(is_enabled)

        config = EmailMarketingConfiguration.current()
        config.sailthru_enabled = False
        config.save()
        is_not_enabled = EmailMarketingConfiguration.current().sailthru_enabled
        self.assertFalse(is_not_enabled)

    @patch('email_marketing.signals.SailthruClient.api_post')
    def test_drop_cookie(self, mock_sailthru):
        """
        Test add_email_marketing_cookies
        """
        response = JsonResponse({
            "success": True,
            "redirect_url": 'test.com/test',
        })
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'keys': {'cookie': 'test_cookie'}}))
        response = add_email_marketing_cookies(response, self.user)
        mock_sailthru.assert_called_with('user', {'fields': {'keys': 1}, 'id': 'test@edx.org'})
        self.assertEquals(response.cookies['sailthru_hid'].value, "test_cookie")

    @patch('email_marketing.signals.SailthruClient.api_post')
    def test_drop_cookie_error_path(self, mock_sailthru):
        """
        test that error paths return no cookie
        """
        response = JsonResponse({
            "success": True,
            "redirect_url": 'test.com/test',
        })
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'keys': {'cookiexx': 'test_cookie'}}))
        response = add_email_marketing_cookies(response, self.user)
        self.assertFalse('sailthru_hid' in response.cookies)

        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': "error", "errormsg": "errormsg"}))
        response = add_email_marketing_cookies(response, self.user)
        self.assertFalse('sailthru_hid' in response.cookies)

        mock_sailthru.side_effect = SailthruClientError
        response = add_email_marketing_cookies(response, self.user)
        self.assertFalse('sailthru_hid' in response.cookies)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.User.objects.get')
    @patch('email_marketing.tasks.UserProfile.objects.get')
    def test_add_user(self, mock_profile_get, mock_user_get, mock_sailthru):
        """
        test async method in tasks that actually updates Sailthru
        """
        mock_user_get.return_value = self.user
        mock_profile_get.return_value = self.profile
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user.delay(self.user.username, new_user=True)
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], "test@edx.org")
        self.assertEquals(userparms['vars']['gender'], "m")
        self.assertEquals(userparms['vars']['username'], "test")
        self.assertEquals(userparms['vars']['activated'], 1)
        self.assertEquals(userparms['lists']['new list'], 1)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.User.objects.get')
    @patch('email_marketing.tasks.UserProfile.objects.get')
    def test_error_logging(self, mock_profile_get, mock_user_get, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_user_get.return_value = self.user
        mock_profile_get.return_value = self.profile
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user.delay(self.user.username)
        self.assertTrue(mock_log_error.called)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.User.objects.get')
    def test_add_user(self, mock_user_get, mock_sailthru):
        """
        test async method in tasks that changes email in Sailthru
        """
        mock_user_get.return_value = self.user
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        self.user.email = "newemail@test.com"
        update_user_email.delay(self.user.username, "test@edx.org")
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], "test@edx.org")
        self.assertEquals(userparms['keys']['email'], "newemail@test.com")

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.User.objects.get')
    def test_error_logging(self, mock_user_get, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_user_get.return_value = self.user
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertTrue(mock_log_error.called)

    @patch('email_marketing.tasks.update_user.delay')
    def test_modify_field1(self, mock_update_user):
        """
        try updating user field
        """
        email_marketing_register_user(None, user=self.user, profile=self.profile)
        self.assertTrue(mock_update_user.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_modify_field1(self, mock_update_user):
        """
        try updating user field
        """
        email_marketing_user_field_changed(None, self.user, table='auth_userprofile', setting='gender', new_value='f')
        self.assertTrue(mock_update_user.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_modify_field2(self, mock_update_user):
        """
        try updating profile field
        """
        email_marketing_user_field_changed(None, self.user, table='auth_user', setting='is_active', new_value=1)
        self.assertTrue(mock_update_user.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_modify_field3(self, mock_update_user):
        """
        try updating unsupported field
        """
        email_marketing_user_field_changed(None, self.user, table='auth_userprofile', setting='shoe_size', new_value=1)
        self.assertFalse(mock_update_user.called)
