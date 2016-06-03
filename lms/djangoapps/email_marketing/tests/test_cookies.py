"""Tests of email marketing signal handlers."""
import logging

from django.test import TestCase
from django.test.utils import override_settings
from mock import patch
from util.json_request import JsonResponse

from email_marketing.cookies import add_email_marketing_cookies
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
        enabled=enabled,
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

    @patch('email_marketing.cookies.SailthruClient.api_post')
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

    @patch('email_marketing.cookies.SailthruClient.api_post')
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
