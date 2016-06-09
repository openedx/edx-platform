"""Tests of email marketing signal handlers."""
import logging
import ddt

from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
from util.json_request import JsonResponse

from email_marketing.signals import handle_unenroll_done, \
    email_marketing_register_user, \
    email_marketing_user_field_changed, \
    add_email_marketing_cookies
from email_marketing.tasks import update_user, update_user_email
from email_marketing.models import EmailMarketingConfiguration
from django.test.client import RequestFactory
from student.tests.factories import UserFactory, UserProfileFactory

from sailthru.sailthru_client import SailthruClient
from sailthru.sailthru_response import SailthruResponse
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)

TEST_EMAIL = "test@edx.org"


def update_email_marketing_config(enabled=False, key='badkey', secret='badsecret', new_user_list='new list',
                                  template='Activation'):
    """
    Enable / Disable Sailthru integration
    """
    EmailMarketingConfiguration.objects.create(
        enabled=enabled,
        sailthru_key=key,
        sailthru_secret=secret,
        sailthru_new_user_list=new_user_list,
        sailthru_activation_template=template
    )


@ddt.ddt
class EmailMarketingTests(TestCase):
    """
    Tests for the EmailMarketing signals and tasks classes.
    """

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = UserFactory.create(username='test', email=TEST_EMAIL)
        self.profile = self.user.profile
        self.request = self.request_factory.get("foo")
        update_email_marketing_config(enabled=True)
        super(EmailMarketingTests, self).setUp()

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
        add_email_marketing_cookies(None, response=response, user=self.user)
        self.assertTrue('sailthru_hid' in response.cookies)
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['fields']['keys'], 1)
        self.assertEquals(userparms['id'], TEST_EMAIL)
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
        add_email_marketing_cookies(None, response=response, user=self.user)
        self.assertFalse('sailthru_hid' in response.cookies)

        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': "error", "errormsg": "errormsg"}))
        add_email_marketing_cookies(None, response=response, user=self.user)
        self.assertFalse('sailthru_hid' in response.cookies)

        mock_sailthru.side_effect = SailthruClientError
        add_email_marketing_cookies(None, response=response, user=self.user)
        self.assertFalse('sailthru_hid' in response.cookies)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_add_user(self, mock_sailthru, mock_log_error):
        """
        test async method in tasks that actually updates Sailthru
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user.delay(self.user.username, new_user=True)
        self.assertFalse(mock_log_error.called)
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], TEST_EMAIL)
        self.assertEquals(userparms['vars']['gender'], "m")
        self.assertEquals(userparms['vars']['username'], "test")
        self.assertEquals(userparms['vars']['activated'], 1)
        self.assertEquals(userparms['lists']['new list'], 1)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_activation(self, mock_sailthru):
        """
        test send of activation template
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user.delay(self.user.username, new_user=True, activation=True)
        # look for call args for 2nd call
        self.assertEquals(mock_sailthru.call_args[0][0], "send")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['email'], TEST_EMAIL)
        self.assertEquals(userparms['template'], "Activation")

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_error_logging(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user.delay(self.user.username)
        self.assertTrue(mock_log_error.called)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_just_return(self, mock_sailthru, mock_log_error):
        """
        Ensure that disabling Sailthru just returns
        """
        update_email_marketing_config(enabled=False)
        update_user.delay(self.user.username)
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)
        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)
        update_email_marketing_config(enabled=True)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_change_email(self, mock_sailthru):
        """
        test async method in task that changes email in Sailthru
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        #self.user.email = "newemail@test.com"
        update_user_email.delay(self.user.username, "old@edx.org")
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], "old@edx.org")
        self.assertEquals(userparms['keys']['email'], TEST_EMAIL)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_error_logging1(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertTrue(mock_log_error.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_register_user(self, mock_update_user):
        """
        make sure register user call invokes update_user
        """
        email_marketing_register_user(None, user=self.user, profile=self.profile)
        self.assertTrue(mock_update_user.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    @ddt.data(('auth_userprofile', 'gender', 'f', True),
              ('auth_user', 'is_active', 1, True),
              ('auth_userprofile', 'shoe_size', 1, False))
    @ddt.unpack
    def test_modify_field(self, table, setting, value, result, mock_update_user):
        """
        Test that correct fields call update_user
        """
        email_marketing_user_field_changed(None, self.user, table=table, setting=setting, new_value=value)
        self.assertEqual(mock_update_user.called, result)
