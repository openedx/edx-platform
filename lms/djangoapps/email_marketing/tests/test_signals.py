"""Tests of email marketing signal handlers."""
import ddt
import logging

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from mock import patch, ANY
from util.json_request import JsonResponse

from email_marketing.signals import handle_enroll_status_change, \
    email_marketing_register_user, \
    email_marketing_user_field_changed, \
    add_email_marketing_cookies
from email_marketing.tasks import (
    update_user_v2, update_user_email, update_course_enrollment,
    _get_course_content, _update_unenrolled_list, _get_or_create_user_list,
    _get_list_from_email_marketing_provider, _create_user_list)

from email_marketing.models import EmailMarketingConfiguration
from django.test.client import RequestFactory
from student.tests.factories import UserFactory, UserProfileFactory
from student.models import EnrollStatusChange
from opaque_keys.edx.keys import CourseKey

from sailthru.sailthru_response import SailthruResponse
from sailthru.sailthru_error import SailthruClientError

log = logging.getLogger(__name__)

TEST_EMAIL = "test@edx.org"


def update_email_marketing_config(enabled=True, key='badkey', secret='badsecret', new_user_list='new list',
                                  template='Activation', enroll_cost=100, lms_url_override='http://testserver'):
    """
    Enable / Disable Sailthru integration
    """
    return EmailMarketingConfiguration.objects.create(
        enabled=enabled,
        sailthru_key=key,
        sailthru_secret=secret,
        sailthru_new_user_list=new_user_list,
        sailthru_activation_template=template,
        sailthru_enroll_template='enroll_template',
        sailthru_lms_url_override=lms_url_override,
        sailthru_get_tags_from_sailthru=False,
        sailthru_enroll_cost=enroll_cost,
        sailthru_max_retries=0,
    )


@ddt.ddt
class EmailMarketingTests(TestCase):
    """
    Tests for the EmailMarketing signals and tasks classes.
    """

    def setUp(self):
        update_email_marketing_config(enabled=False)
        self.request_factory = RequestFactory()
        self.user = UserFactory.create(username='test', email=TEST_EMAIL)
        self.profile = self.user.profile
        self.profile.year_of_birth = 1980
        self.profile.save()

        self.request = self.request_factory.get("foo")
        update_email_marketing_config(enabled=True)

        # create some test course objects
        self.course_id_string = 'edX/toy/2012_Fall'
        self.course_id = CourseKey.from_string(self.course_id_string)
        self.course_url = 'http://testserver/courses/edX/toy/2012_Fall/info'

        self.site = Site.objects.get_current()
        self.site_domain = self.site.domain
        self.request.site = self.site
        super(EmailMarketingTests, self).setUp()

    @patch('email_marketing.signals.crum.get_current_request')
    @patch('email_marketing.signals.SailthruClient.api_post')
    def test_drop_cookie(self, mock_sailthru, mock_get_current_request):
        """
        Test add_email_marketing_cookies
        """
        response = JsonResponse({
            "success": True,
            "redirect_url": 'test.com/test',
        })
        self.request.COOKIES['sailthru_content'] = 'cookie_content'
        mock_get_current_request.return_value = self.request
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'keys': {'cookie': 'test_cookie'}}))
        add_email_marketing_cookies(None, response=response, user=self.user)
        mock_sailthru.assert_called_with('user',
                                         {'fields': {'keys': 1},
                                          'cookies': {'sailthru_content': 'cookie_content'},
                                          'id': TEST_EMAIL,
                                          'vars': {'last_login_date': ANY}})
        self.assertTrue('sailthru_hid' in response.cookies)
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
    @patch('email_marketing.tasks.SailthruClient.api_get')
    def test_add_user(self, mock_sailthru_get, mock_sailthru_post, mock_log_error):
        """
        test async method in tasks that actually updates Sailthru
        """
        site_dict = {'id': self.site.id, 'domain': self.site.domain, 'name': self.site.name}
        mock_sailthru_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        mock_sailthru_get.return_value = SailthruResponse(JsonResponse({'lists': [{'name': 'new list'}], 'ok': True}))
        update_user_v2.delay(
            {'gender': 'm', 'username': 'test', 'activated': 1}, TEST_EMAIL, site_dict, new_user=True
        )
        self.assertFalse(mock_log_error.called)
        self.assertEquals(mock_sailthru_post.call_args[0][0], "user")
        userparms = mock_sailthru_post.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], TEST_EMAIL)
        self.assertEquals(userparms['vars']['gender'], "m")
        self.assertEquals(userparms['vars']['username'], "test")
        self.assertEquals(userparms['vars']['activated'], 1)
        self.assertEquals(userparms['lists']['new list'], 1)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.SailthruClient.api_get')
    def test_add_user_list_existing_domain(self, mock_sailthru_get, mock_sailthru_post):
        """
        test non existing domain name updates Sailthru user lists with default list
        """
        existing_site = Site.objects.create(domain='testing.com', name='testing.com')
        site_dict = {'id': existing_site.id, 'domain': existing_site.domain, 'name': existing_site.name}
        mock_sailthru_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        mock_sailthru_get.return_value = SailthruResponse(
            JsonResponse({'lists': [{'name': 'new list'}, {'name': 'testing_com_user_list'}], 'ok': True})
        )
        update_user_v2.delay(
            {'gender': 'm', 'username': 'test', 'activated': 1}, TEST_EMAIL, site=site_dict, new_user=True
        )
        self.assertEquals(mock_sailthru_post.call_args[0][0], "user")
        userparms = mock_sailthru_post.call_args[0][1]
        self.assertEquals(userparms['lists']['testing_com_user_list'], 1)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.SailthruClient.api_get')
    def test_user_activation(self, mock_sailthru_get, mock_sailthru_post):
        """
        test send of activation template
        """
        mock_sailthru_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        mock_sailthru_get.return_value = SailthruResponse(JsonResponse({'lists': [{'name': 'new list'}], 'ok': True}))
        update_user_v2.delay({}, self.user.email, new_user=True, activation=True)
        # look for call args for 2nd call
        self.assertEquals(mock_sailthru_post.call_args[0][0], "send")
        userparms = mock_sailthru_post.call_args[0][1]
        self.assertEquals(userparms['email'], TEST_EMAIL)
        self.assertEquals(userparms['template'], "Activation")

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_logging(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user_v2.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API exception
        mock_log_error.reset_mock()
        mock_sailthru.side_effect = SailthruClientError
        update_user_v2.delay({}, self.user.email, self.site_domain)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API exception on 2nd call
        mock_log_error.reset_mock()
        mock_sailthru.side_effect = [SailthruResponse(JsonResponse({'ok': True})), SailthruClientError]
        update_user_v2.delay({}, self.user.email, activation=True)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API error return on 2nd call
        mock_log_error.reset_mock()
        mock_sailthru.side_effect = [SailthruResponse(JsonResponse({'ok': True})),
                                     SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))]
        update_user_v2.delay({}, self.user.email, activation=True)
        self.assertTrue(mock_log_error.called)

    @patch('email_marketing.tasks.update_user_v2.retry')
    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_retryable(self, mock_sailthru, mock_log_error, mock_retry):
        """
        Ensure that retryable error is retried
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 43, 'errormsg': 'Got an error'}))
        update_user_v2.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)
        self.assertTrue(mock_retry.called)

    @patch('email_marketing.tasks.update_user_v2.retry')
    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_nonretryable(self, mock_sailthru, mock_log_error, mock_retry):
        """
        Ensure that non-retryable error is not retried
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 1, 'errormsg': 'Got an error'}))
        update_user_v2.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)
        self.assertFalse(mock_retry.called)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_just_return_tasks(self, mock_sailthru, mock_log_error):
        """
        Ensure that disabling Sailthru just returns
        """
        update_email_marketing_config(enabled=False)

        update_user_v2.delay(self.user.username)
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

        update_course_enrollment.delay(self.user.username, TEST_EMAIL, 'http://course',
                                       EnrollStatusChange.enroll, 'audit')
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

        update_email_marketing_config(enabled=True)

    @patch('email_marketing.signals.log.error')
    def test_just_return_signals(self, mock_log_error):
        """
        Ensure that disabling Sailthru just returns
        """
        update_email_marketing_config(enabled=False)

        handle_enroll_status_change(None)
        self.assertFalse(mock_log_error.called)

        add_email_marketing_cookies(None)
        self.assertFalse(mock_log_error.called)

        email_marketing_register_user(None)
        self.assertFalse(mock_log_error.called)

        update_email_marketing_config(enabled=True)

        # test anonymous users
        anon = AnonymousUser()
        email_marketing_register_user(None, user=anon)
        self.assertFalse(mock_log_error.called)

        email_marketing_user_field_changed(None, user=anon)
        self.assertFalse(mock_log_error.called)

        # make sure enroll ignored when cost = 0
        update_email_marketing_config(enroll_cost=0)
        handle_enroll_status_change(None, event=EnrollStatusChange.enroll,
                                    user=self.user,
                                    mode='audit', course_id=self.course_id)
        self.assertFalse(mock_log_error.called)

    @patch('email_marketing.signals.crum.get_current_request')
    @patch('lms.djangoapps.email_marketing.tasks.update_course_enrollment.delay')
    def test_handle_enroll_status_change(self, mock_update_course_enrollment, mock_get_current_request):
        """
        Test that the enroll status change signal handler properly calls the task routine
        """
        # should just return if no current request found
        mock_get_current_request.return_value = None
        handle_enroll_status_change(None)
        self.assertFalse(mock_update_course_enrollment.called)

        # now test with current request
        mock_get_current_request.return_value = self.request
        self.request.COOKIES['sailthru_bid'] = 'cookie_bid'
        handle_enroll_status_change(None, event=EnrollStatusChange.enroll,
                                    user=self.user,
                                    mode='audit', course_id=self.course_id,
                                    cost=None, currency=None)
        self.assertTrue(mock_update_course_enrollment.called)
        mock_update_course_enrollment.assert_called_with(TEST_EMAIL,
                                                         self.course_url,
                                                         EnrollStatusChange.enroll,
                                                         'audit',
                                                         course_id=self.course_id_string,
                                                         message_id='cookie_bid')

        # now test with current request constructing url from request
        mock_get_current_request.return_value = self.request
        update_email_marketing_config(lms_url_override='')
        self.request.COOKIES['sailthru_bid'] = 'cookie_bid'
        handle_enroll_status_change(None, event=EnrollStatusChange.enroll,
                                    user=self.user,
                                    mode='audit', course_id=self.course_id,
                                    cost=None, currency=None)
        self.assertTrue(mock_update_course_enrollment.called)
        mock_update_course_enrollment.assert_called_with(TEST_EMAIL,
                                                         self.course_url,
                                                         EnrollStatusChange.enroll,
                                                         'audit',
                                                         course_id=self.course_id_string,
                                                         message_id='cookie_bid')

    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_change_email(self, mock_sailthru):
        """
        test async method in task that changes email in Sailthru
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user_email.delay(TEST_EMAIL, "old@edx.org")
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], "old@edx.org")
        self.assertEquals(userparms['keys']['email'], TEST_EMAIL)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.log.info')
    @patch('email_marketing.tasks.SailthruClient.purchase')
    @patch('email_marketing.tasks.SailthruClient.api_get')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_update_course_enrollment(self, mock_sailthru_api_post,
                                      mock_sailthru_api_get, mock_sailthru_purchase, mock_log_info, mock_log_error):
        """
        test async method in task posts enrolls and purchases
        """

        mock_sailthru_api_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        mock_sailthru_api_get.return_value = SailthruResponse(JsonResponse({'vars': {'unenrolled': ['course_u1']}}))
        mock_sailthru_purchase.return_value = SailthruResponse(JsonResponse({'ok': True}))

        # test enroll
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.enroll,
                                       'audit',
                                       course_id=self.course_id_string,
                                       message_id='cookie_bid')
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'audit'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: audit',
                                                                'url': self.course_url,
                                                                'price': 100, 'qty': 1, 'id': self.course_id_string + '-audit'}],
                                                  options={'send_template': 'enroll_template'},
                                                  message_id='cookie_bid')

        # test unenroll
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.unenroll,
                                       'audit',
                                       course_id=self.course_id_string,
                                       message_id='cookie_bid')
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'audit'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: audit',
                                                                'url': self.course_url,
                                                                'price': 100, 'qty': 1, 'id': self.course_id_string + '-audit'}],
                                                  options={'send_template': 'enroll_template'},
                                                  message_id='cookie_bid')

        # test purchase API error
        mock_sailthru_purchase.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.enroll,
                                       'verified',
                                       course_id=self.course_id_string,
                                       message_id='cookie_bid')
        self.assertTrue(mock_log_error.called)

        # test purchase API exception
        mock_sailthru_purchase.side_effect = SailthruClientError
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.enroll,
                                       'verified',
                                       course_id=self.course_id_string,
                                       message_id='cookie_bid')
        self.assertTrue(mock_log_error.called)

        # test unsupported event
        mock_sailthru_purchase.side_effect = SailthruClientError
        mock_log_info.reset_mock()
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.upgrade_start,
                                       'verified',
                                       course_id=self.course_id_string,
                                       message_id='cookie_bid')
        self.assertFalse(mock_log_info.called)

        # test error updating user
        mock_sailthru_api_get.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.enroll,
                                       'verified',
                                       course_id=self.course_id_string,
                                       message_id='cookie_bid')
        self.assertTrue(mock_log_info.called)

    @patch('email_marketing.tasks.SailthruClient')
    def test_get_course_content(self, mock_sailthru_client):
        """
        test routine which fetches data from Sailthru content api
        """
        mock_sailthru_client.api_get.return_value = SailthruResponse(JsonResponse({"title": "The title"}))
        response_json = _get_course_content('course:123', mock_sailthru_client, EmailMarketingConfiguration.current())
        self.assertEquals(response_json, {"title": "The title"})
        mock_sailthru_client.api_get.assert_called_with('content', {'id': 'course:123'})

        # test second call uses cache
        response_json = _get_course_content('course:123', mock_sailthru_client, EmailMarketingConfiguration.current())
        self.assertEquals(response_json, {"title": "The title"})
        mock_sailthru_client.api_get.assert_not_called()

        # test error from Sailthru
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        self.assertEquals(_get_course_content('course:124', mock_sailthru_client, EmailMarketingConfiguration.current()), {})

        # test exception
        mock_sailthru_client.api_get.side_effect = SailthruClientError
        self.assertEquals(_get_course_content('course:125', mock_sailthru_client, EmailMarketingConfiguration.current()), {})

    @patch('email_marketing.tasks.SailthruClient')
    def test_update_unenrolled_list(self, mock_sailthru_client):
        """
        test routine which updates the unenrolled list in Sailthru
        """

        # test a new unenroll
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'vars': {'unenrolled': ['course_u1']}}))
        self.assertTrue(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                self.course_url, True))
        mock_sailthru_client.api_get.assert_called_with("user", {"id": TEST_EMAIL, "fields": {"vars": 1}})
        mock_sailthru_client.api_post.assert_called_with('user',
                                                         {'vars': {'unenrolled': ['course_u1', self.course_url]},
                                                          'id': TEST_EMAIL, 'key': 'email'})

        # test an enroll of a previously unenrolled course
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'vars': {'unenrolled': [self.course_url]}}))
        self.assertTrue(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                self.course_url, False))
        mock_sailthru_client.api_post.assert_called_with('user',
                                                         {'vars': {'unenrolled': []},
                                                          'id': TEST_EMAIL, 'key': 'email'})

        # test get error from Sailthru
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'error': 43, 'errormsg': 'Got an error'}))
        self.assertFalse(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                 self.course_url, False))

        # test post error from Sailthru
        mock_sailthru_client.api_post.return_value = \
            SailthruResponse(JsonResponse({'error': 43, 'errormsg': 'Got an error'}))
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'vars': {'unenrolled': [self.course_url]}}))
        self.assertFalse(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                 self.course_url, False))

        # test exception
        mock_sailthru_client.api_get.side_effect = SailthruClientError
        self.assertFalse(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                 self.course_url, False))

    @patch('email_marketing.tasks.SailthruClient')
    def test_get_or_create_sailthru_list(self, mock_sailthru_client):
        """
        Test the task the create sailthru lists.
        """
        mock_sailthru_client.api_get.return_value = SailthruResponse(JsonResponse({'lists': []}))
        _get_or_create_user_list(mock_sailthru_client, 'test1_user_list')
        mock_sailthru_client.api_get.assert_called_with("list", {})
        mock_sailthru_client.api_post.assert_called_with(
            "list", {'list': 'test1_user_list', 'primary': 0, 'public_name': 'test1_user_list'}
        )

        # test existing user list
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'lists': [{'name': 'test1_user_list'}]}))
        _get_or_create_user_list(mock_sailthru_client, 'test2_user_list')
        mock_sailthru_client.api_get.assert_called_with("list", {})
        mock_sailthru_client.api_post.assert_called_with(
            "list", {'list': 'test2_user_list', 'primary': 0, 'public_name': 'test2_user_list'}
        )

        # test get error from Sailthru
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'error': 43, 'errormsg': 'Got an error'}))
        self.assertEqual(_get_or_create_user_list(
            mock_sailthru_client, 'test1_user_list'), None
        )

        # test post error from Sailthru
        mock_sailthru_client.api_post.return_value = \
            SailthruResponse(JsonResponse({'error': 43, 'errormsg': 'Got an error'}))
        mock_sailthru_client.api_get.return_value = SailthruResponse(JsonResponse({'lists': []}))
        self.assertEqual(_get_or_create_user_list(mock_sailthru_client, 'test2_user_list'), None)

    @patch('email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list_map_no_list(self, mock_sailthru_client):
        """Test when no list returned from sailthru"""
        mock_sailthru_client.api_get.return_value = SailthruResponse(JsonResponse({'lists': []}))
        self.assertEqual(_get_list_from_email_marketing_provider(mock_sailthru_client), {})
        mock_sailthru_client.api_get.assert_called_with("list", {})

    @patch('email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list_map_error(self, mock_sailthru_client):
        """Test when error occurred while fetching data from sailthru"""
        mock_sailthru_client.api_get.return_value = SailthruResponse(
            JsonResponse({'error': 43, 'errormsg': 'Got an error'})
        )
        self.assertEqual(_get_list_from_email_marketing_provider(mock_sailthru_client), {})

    @patch('email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list_map_exception(self, mock_sailthru_client):
        """Test when exception raised while fetching data from sailthru"""
        mock_sailthru_client.api_get.side_effect = SailthruClientError
        self.assertEqual(_get_list_from_email_marketing_provider(mock_sailthru_client), {})

    @patch('email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list(self, mock_sailthru_client):
        """Test fetch list data from sailthru"""
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'lists': [{'name': 'test1_user_list'}]}))
        self.assertEqual(
            _get_list_from_email_marketing_provider(mock_sailthru_client),
            {'test1_user_list': {'name': 'test1_user_list'}}
        )
        mock_sailthru_client.api_get.assert_called_with("list", {})

    @patch('email_marketing.tasks.SailthruClient')
    def test_create_sailthru_list(self, mock_sailthru_client):
        """Test create list in sailthru"""
        mock_sailthru_client.api_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        self.assertEqual(_create_user_list(mock_sailthru_client, 'test_list_name'), True)
        self.assertEquals(mock_sailthru_client.api_post.call_args[0][0], "list")
        listparms = mock_sailthru_client.api_post.call_args[0][1]
        self.assertEqual(listparms['list'], 'test_list_name')
        self.assertEqual(listparms['primary'], 0)
        self.assertEqual(listparms['public_name'], 'test_list_name')

    @patch('email_marketing.tasks.SailthruClient')
    def test_create_sailthru_list_error(self, mock_sailthru_client):
        """Test error occurrence while creating sailthru list"""
        mock_sailthru_client.api_post.return_value = SailthruResponse(
            JsonResponse({'error': 43, 'errormsg': 'Got an error'})
        )
        self.assertEqual(_create_user_list(mock_sailthru_client, 'test_list_name'), False)

    @patch('email_marketing.tasks.SailthruClient')
    def test_create_sailthru_list_exception(self, mock_sailthru_client):
        """Test exception raised while creating sailthru list"""
        mock_sailthru_client.api_post.side_effect = SailthruClientError
        self.assertEqual(_create_user_list(mock_sailthru_client, 'test_list_name'), False)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_error_logging(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertTrue(mock_log_error.called)

        mock_sailthru.side_effect = SailthruClientError
        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertTrue(mock_log_error.called)

    @patch('email_marketing.signals.crum.get_current_request')
    @patch('lms.djangoapps.email_marketing.tasks.update_user_v2.delay')
    def test_register_user(self, mock_update_user, mock_get_current_request):
        """
        make sure register user call invokes update_user
        """
        mock_get_current_request.return_value = self.request
        email_marketing_register_user(None, user=self.user, profile=self.profile)
        self.assertTrue(mock_update_user.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user_v2.delay')
    def test_register_user_no_request(self, mock_update_user):
        """
        make sure register user call invokes update_user
        """
        email_marketing_register_user(None, user=self.user, profile=self.profile)
        self.assertTrue(mock_update_user.called)

    @patch('email_marketing.signals.crum.get_current_request')
    @patch('lms.djangoapps.email_marketing.tasks.update_user_v2.delay')
    @ddt.data(('auth_userprofile', 'gender', 'f', True),
              ('auth_user', 'is_active', 1, True),
              ('auth_userprofile', 'shoe_size', 1, False))
    @ddt.unpack
    def test_modify_field(self, table, setting, value, result, mock_update_user, mock_get_current_request):
        """
        Test that correct fields call update_user
        """
        mock_get_current_request.return_value = self.request
        email_marketing_user_field_changed(None, self.user, table=table, setting=setting, new_value=value)
        self.assertEqual(mock_update_user.called, result)

    @patch('lms.djangoapps.email_marketing.tasks.update_user_email.delay')
    def test_modify_email(self, mock_update_user):
        """
        Test that change to email calls update_user_email
        """
        email_marketing_user_field_changed(None, self.user, table='auth_user', setting='email', old_value='new@a.com')
        mock_update_user.assert_called_with(self.user.email, 'new@a.com')

        # make sure nothing called if disabled
        mock_update_user.reset_mock()
        update_email_marketing_config(enabled=False)
        email_marketing_user_field_changed(None, self.user, table='auth_user', setting='email', old_value='new@a.com')
        self.assertFalse(mock_update_user.called)
