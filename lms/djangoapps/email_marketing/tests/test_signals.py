"""Tests of email marketing signal handlers."""
import logging
import ddt
import datetime

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from mock import patch, ANY
from util.json_request import JsonResponse
from django.http import Http404

from email_marketing.signals import handle_enroll_status_change, \
    email_marketing_register_user, \
    email_marketing_user_field_changed, \
    add_email_marketing_cookies
from email_marketing.tasks import update_user, update_user_email, update_course_enrollment, \
    _get_course_content, _update_unenrolled_list
from email_marketing.models import EmailMarketingConfiguration
from django.test.client import RequestFactory
from student.tests.factories import UserFactory, UserProfileFactory
from request_cache.middleware import RequestCache
from student.models import EnrollStatusChange
from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode
from xmodule.modulestore.tests.factories import CourseFactory

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
        sailthru_activation_template=template,
        sailthru_enroll_template='enroll_template',
        sailthru_upgrade_template='upgrade_template',
        sailthru_purchase_template='purchase_template',
        sailthru_abandoned_cart_template='abandoned_template',
        sailthru_get_tags_from_sailthru=False
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

        # create some test course objects
        self.course_id_string = 'edX/toy/2012_Fall'
        self.course_id = CourseKey.from_string(self.course_id_string)
        self.course_url = 'http://testserver/courses/edX/toy/2012_Fall/info'
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
    def test_user_activation(self, mock_sailthru):
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
    def test_update_user_error_logging(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user.delay(self.user.username)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API exception
        mock_sailthru.side_effect = SailthruClientError
        update_user.delay(self.user.username)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API exception on 2nd call
        mock_sailthru.side_effect = [None, SailthruClientError]
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user.delay(self.user.username, new_user=True)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API error return on 2nd call
        mock_sailthru.side_effect = None
        mock_sailthru.return_value = [SailthruResponse(JsonResponse({'ok': True})),
                                      SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))]
        update_user.delay(self.user.username, new_user=True)
        self.assertTrue(mock_log_error.called)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_logging_bad_user(self, mock_sailthru, mock_log_error):
        """
        Test update_user with invalid user
        """
        update_user.delay('baduser')
        self.assertTrue(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

        update_user_email.delay('baduser', 'aa@bb.com')
        self.assertTrue(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_just_return_tasks(self, mock_sailthru, mock_log_error):
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
                                                         course_id=self.course_id,
                                                         currency=None,
                                                         message_id='cookie_bid',
                                                         unit_cost=None)

    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_change_email(self, mock_sailthru):
        """
        test async method in task that changes email in Sailthru
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user_email.delay(self.user.username, "old@edx.org")
        self.assertEquals(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEquals(userparms['key'], "email")
        self.assertEquals(userparms['id'], "old@edx.org")
        self.assertEquals(userparms['keys']['email'], TEST_EMAIL)

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.purchase')
    @patch('email_marketing.tasks.SailthruClient.api_get')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    @patch('email_marketing.tasks.get_course_by_id')
    def test_update_course_enrollment(self, mock_get_course, mock_sailthru_api_post,
                                      mock_sailthru_api_get, mock_sailthru_purchase, mock_log_error):
        """
        test async method in task posts enrolls and purchases
        """

        CourseMode.objects.create(
            course_id=self.course_id,
            mode_slug=CourseMode.AUDIT,
            mode_display_name=CourseMode.AUDIT
        )
        CourseMode.objects.create(
            course_id=self.course_id,
            mode_slug=CourseMode.VERIFIED,
            mode_display_name=CourseMode.VERIFIED,
            min_price=49,
            expiration_datetime=datetime.date(2020, 3, 12)
        )
        mock_get_course.return_value = {'display_name': "Test Title"}
        mock_sailthru_api_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        mock_sailthru_api_get.return_value = SailthruResponse(JsonResponse({'vars': {'unenrolled': ['course_u1']}}))
        mock_sailthru_purchase.return_value = SailthruResponse(JsonResponse({'ok': True}))

        # test enroll
        mock_get_course.side_effect = Http404
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.enroll,
                                       'audit',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=0)
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'audit',
                                                                         'upgrade_deadline_verified': '2020-03-12'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: audit',
                                                                'url': self.course_url,
                                                                'price': 100, 'qty': 1, 'id': self.course_id_string + '-audit'}],
                                                  options={'send_template': 'enroll_template'},
                                                  incomplete=None, message_id='cookie_bid')

        # test unenroll
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.unenroll,
                                       'audit',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=0)
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'audit',
                                                                         'upgrade_deadline_verified': '2020-03-12'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: audit',
                                                                'url': self.course_url,
                                                                'price': 100, 'qty': 1, 'id': self.course_id_string + '-audit'}],
                                                  options={'send_template': 'enroll_template'},
                                                  incomplete=None, message_id='cookie_bid')

        # test add upgrade to cart
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.upgrade_start,
                                       'verified',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=49)
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'verified',
                                                                         'upgrade_deadline_verified': '2020-03-12'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: verified',
                                                                'url': self.course_url,
                                                                'price': 4900, 'qty': 1, 'id': self.course_id_string + '-verified'}],
                                                  options={'reminder_template': 'abandoned_template', 'reminder_time': '+60 minutes'},
                                                  incomplete=1, message_id='cookie_bid')

        # test add purchase to cart
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.paid_start,
                                       'honor',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=49)
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'honor',
                                                                         'upgrade_deadline_verified': '2020-03-12'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: honor',
                                                                'url': self.course_url,
                                                                'price': 4900, 'qty': 1, 'id': self.course_id_string + '-honor'}],
                                                  options={'reminder_template': 'abandoned_template', 'reminder_time': '+60 minutes'},
                                                  incomplete=1, message_id='cookie_bid')

        # test purchase complete
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.paid_complete,
                                       'honor',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=99)
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'honor',
                                                                         'upgrade_deadline_verified': '2020-03-12'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: honor',
                                                                'url': self.course_url,
                                                                'price': 9900, 'qty': 1, 'id': self.course_id_string + '-honor'}],
                                                  options={'send_template': 'purchase_template'},
                                                  incomplete=None, message_id='cookie_bid')

        # test upgrade complete
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.upgrade_complete,
                                       'verified',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=99)
        mock_sailthru_purchase.assert_called_with(TEST_EMAIL, [{'vars': {'course_run_id': self.course_id_string, 'mode': 'verified',
                                                                         'upgrade_deadline_verified': '2020-03-12'},
                                                                'title': 'Course ' + self.course_id_string + ' mode: verified',
                                                                'url': self.course_url,
                                                                'price': 9900, 'qty': 1, 'id': self.course_id_string + '-verified'}],
                                                  options={'send_template': 'upgrade_template'},
                                                  incomplete=None, message_id='cookie_bid')

        # test purchase API error
        mock_sailthru_purchase.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.upgrade_complete,
                                       'verified',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=99)
        self.assertTrue(mock_log_error.called)

        # test purchase API exception
        mock_sailthru_purchase.side_effect = SailthruClientError
        update_course_enrollment.delay(TEST_EMAIL,
                                       self.course_url,
                                       EnrollStatusChange.upgrade_complete,
                                       'verified',
                                       course_id=self.course_id,
                                       currency='USD',
                                       message_id='cookie_bid',
                                       unit_cost=99)
        self.assertTrue(mock_log_error.called)

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
            SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        self.assertFalse(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                 self.course_url, False))

        # test post error from Sailthru
        mock_sailthru_client.api_post.return_value = \
            SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'vars': {'unenrolled': [self.course_url]}}))
        self.assertFalse(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                 self.course_url, False))

        # test exception
        mock_sailthru_client.api_get.side_effect = SailthruClientError
        self.assertFalse(_update_unenrolled_list(mock_sailthru_client, TEST_EMAIL,
                                                 self.course_url, False))

    @patch('email_marketing.tasks.log.error')
    @patch('email_marketing.tasks.SailthruClient.api_post')
    def test_error_logging1(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertTrue(mock_log_error.called)

        mock_sailthru.side_effect = SailthruClientError
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
