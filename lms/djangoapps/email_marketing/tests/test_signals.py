# -*- coding: utf-8 -*-

"""Tests of email marketing signal handlers."""


import datetime
import logging

import ddt
import six
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.test import TestCase
from django.test.client import RequestFactory
from freezegun import freeze_time
from mock import ANY, Mock, patch
from opaque_keys.edx.keys import CourseKey
from sailthru.sailthru_error import SailthruClientError
from sailthru.sailthru_response import SailthruResponse
from testfixtures import LogCapture

from lms.djangoapps.email_marketing.tasks import (
    _create_user_list,
    _get_list_from_email_marketing_provider,
    _get_or_create_user_list,
    get_email_cookies_via_sailthru,
    update_course_enrollment,
    update_user,
    update_user_email
)
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from common.djangoapps.student.models import Registration
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory, UserProfileFactory
from common.djangoapps.util.json_request import JsonResponse

from ..models import EmailMarketingConfiguration
from ..signals import (
    add_email_marketing_cookies,
    email_marketing_register_user,
    email_marketing_user_field_changed,
    update_sailthru
)

log = logging.getLogger(__name__)

LOGGER_NAME = "lms.djangoapps.email_marketing.signals"

TEST_EMAIL = "test@edx.org"


def update_email_marketing_config(enabled=True, key='badkey', secret='badsecret', new_user_list='new list',
                                  template='Welcome', enroll_cost=100, lms_url_override='http://testserver'):
    """
    Enable / Disable Sailthru integration
    """
    return EmailMarketingConfiguration.objects.create(
        enabled=enabled,
        sailthru_key=key,
        sailthru_secret=secret,
        sailthru_new_user_list=new_user_list,
        sailthru_welcome_template=template,
        sailthru_enroll_template='enroll_template',
        sailthru_lms_url_override=lms_url_override,
        sailthru_get_tags_from_sailthru=False,
        sailthru_enroll_cost=enroll_cost,
        sailthru_max_retries=0,
        welcome_email_send_delay=600
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
        self.registration = Registration()
        self.registration.register(self.user)

        self.request = self.request_factory.get("foo")
        update_email_marketing_config(enabled=True)

        # create some test course objects
        self.course_id_string = 'edX/toy/2012_Fall'
        self.course_id = CourseKey.from_string(self.course_id_string)
        self.course_url = 'http://testserver/courses/edX/toy/2012_Fall/info'

        self.site = Site.objects.get_current()
        self.request.site = self.site
        super(EmailMarketingTests, self).setUp()

    @freeze_time(datetime.datetime.now())
    @patch('lms.djangoapps.email_marketing.signals.crum.get_current_request')
    @patch('sailthru.sailthru_client.SailthruClient.api_post')
    def test_drop_cookie(self, mock_sailthru, mock_get_current_request):
        """
        Test add_email_marketing_cookies
        """
        response = JsonResponse({
            "success": True,
            "redirect_url": 'test.com/test',
        })
        self.request.COOKIES['anonymous_interest'] = 'cookie_content'
        mock_get_current_request.return_value = self.request

        cookies = {'cookie': 'test_cookie'}
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'keys': cookies}))

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            add_email_marketing_cookies(None, response=response, user=self.user)
            logger.check(
                (LOGGER_NAME, 'INFO',
                    'Started at {start} and ended at {end}, time spent:{delta} milliseconds'.format(
                        start=datetime.datetime.now().isoformat(' '),
                        end=datetime.datetime.now().isoformat(' '),
                        delta=0 if six.PY2 else 0.0)
                 ),
                (LOGGER_NAME, 'INFO',
                    'sailthru_hid cookie:{cookies[cookie]} successfully retrieved for user {user}'.format(
                        cookies=cookies,
                        user=TEST_EMAIL)
                 )
            )
        mock_sailthru.assert_called_with('user',
                                         {'fields': {'keys': 1},
                                          'cookies': {'anonymous_interest': 'cookie_content'},
                                          'id': TEST_EMAIL,
                                          'vars': {'last_login_date': ANY}})
        self.assertTrue('sailthru_hid' in response.cookies)
        self.assertEqual(response.cookies['sailthru_hid'].value, "test_cookie")

    @patch('sailthru.sailthru_client.SailthruClient.api_post')
    def test_get_cookies_via_sailthu(self, mock_sailthru):

        cookies = {'cookie': 'test_cookie'}
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'keys': cookies}))

        post_parms = {
            'id': self.user.email,
            'fields': {'keys': 1},
            'vars': {'last_login_date': datetime.datetime.now().strftime("%Y-%m-%d")},
            'cookies': {'anonymous_interest': 'cookie_content'}
        }
        expected_cookie = get_email_cookies_via_sailthru.delay(self.user.email, post_parms)

        mock_sailthru.assert_called_with('user',
                                         {'fields': {'keys': 1},
                                          'cookies': {'anonymous_interest': 'cookie_content'},
                                          'id': TEST_EMAIL,
                                          'vars': {'last_login_date': ANY}})

        self.assertEqual(cookies['cookie'], expected_cookie.result)

    @patch('sailthru.sailthru_client.SailthruClient.api_post')
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

    @patch('lms.djangoapps.email_marketing.tasks.log.error')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_get')
    def test_add_user(self, mock_sailthru_get, mock_sailthru_post, mock_log_error):
        """
        test async method in tasks that actually updates Sailthru
        """
        site_dict = {'id': self.site.id, 'domain': self.site.domain, 'name': self.site.name}
        mock_sailthru_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        mock_sailthru_get.return_value = SailthruResponse(JsonResponse({'lists': [{'name': 'new list'}], 'ok': True}))
        update_user.delay(
            {'gender': 'm', 'username': 'test', 'activated': 1}, TEST_EMAIL, site_dict, new_user=True
        )
        self.assertFalse(mock_log_error.called)
        self.assertEqual(mock_sailthru_post.call_args[0][0], "user")
        userparms = mock_sailthru_post.call_args[0][1]
        self.assertEqual(userparms['key'], "email")
        self.assertEqual(userparms['id'], TEST_EMAIL)
        self.assertEqual(userparms['vars']['gender'], "m")
        self.assertEqual(userparms['vars']['username'], "test")
        self.assertEqual(userparms['vars']['activated'], 1)
        self.assertEqual(userparms['lists']['new list'], 1)

    @patch('lms.djangoapps.email_marketing.signals.get_email_cookies_via_sailthru.delay')
    def test_drop_cookie_task_error(self, mock_email_cookies):
        """
        Tests that task error is handled
        """
        mock_email_cookies.return_value = {}
        mock_email_cookies.get.side_effect = Exception
        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            add_email_marketing_cookies(None, response=None, user=self.user)
            logger.check((
                LOGGER_NAME, 'ERROR', 'Exception Connecting to celery task for {}'.format(
                    self.user.email
                )
            ))

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_email_not_sent_to_enterprise_learners(self, mock_sailthru_post):
        """
        tests that welcome email is not sent to the enterprise learner
        """
        mock_sailthru_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user.delay(
            sailthru_vars={
                'is_enterprise_learner': True,
                'enterprise_name': 'test name',
            },
            email=self.user.email
        )
        self.assertNotEqual(mock_sailthru_post.call_args[0][0], "send")

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_add_user_list_not_called_on_white_label_domain(self, mock_sailthru_post):
        """
        test user is not added to Sailthru user lists if registered from a whitel labe site
        """
        existing_site = Site.objects.create(domain='testwhitelabel.com', name='White Label')
        site_dict = {'id': existing_site.id, 'domain': existing_site.domain, 'name': existing_site.name}
        update_user.delay(
            {'gender': 'm', 'username': 'test', 'activated': 1}, TEST_EMAIL, site=site_dict, new_user=True
        )
        self.assertFalse(mock_sailthru_post.called)

    @patch('lms.djangoapps.email_marketing.tasks.log.error')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_logging(self, mock_sailthru, mock_log_error):
        """
        Ensure that error returned from Sailthru api is logged
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))
        update_user.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API exception
        mock_log_error.reset_mock()
        mock_sailthru.side_effect = SailthruClientError
        update_user.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API exception on 2nd call
        mock_log_error.reset_mock()
        mock_sailthru.side_effect = [SailthruResponse(JsonResponse({'ok': True})), SailthruClientError]
        update_user.delay({}, self.user.email, activation=True)
        self.assertTrue(mock_log_error.called)

        # force Sailthru API error return on 2nd call
        mock_log_error.reset_mock()
        mock_sailthru.side_effect = [SailthruResponse(JsonResponse({'ok': True})),
                                     SailthruResponse(JsonResponse({'error': 100, 'errormsg': 'Got an error'}))]
        update_user.delay({}, self.user.email, activation=True)
        self.assertTrue(mock_log_error.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.retry')
    @patch('lms.djangoapps.email_marketing.tasks.log.error')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_retryable(self, mock_sailthru, mock_log_error, mock_retry):
        """
        Ensure that retryable error is retried
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 43, 'errormsg': 'Got an error'}))
        update_user.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)
        self.assertTrue(mock_retry.called)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.retry')
    @patch('lms.djangoapps.email_marketing.tasks.log.error')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_update_user_error_nonretryable(self, mock_sailthru, mock_log_error, mock_retry):
        """
        Ensure that non-retryable error is not retried
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'error': 1, 'errormsg': 'Got an error'}))
        update_user.delay({}, self.user.email)
        self.assertTrue(mock_log_error.called)
        self.assertFalse(mock_retry.called)

    @patch('lms.djangoapps.email_marketing.tasks.log.error')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_just_return_tasks(self, mock_sailthru, mock_log_error):
        """
        Ensure that disabling Sailthru just returns
        """
        update_email_marketing_config(enabled=False)

        update_user.delay(self.user.username, self.user.email)
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

        update_user_email.delay(self.user.username, "newemail2@test.com")
        self.assertFalse(mock_log_error.called)
        self.assertFalse(mock_sailthru.called)

        update_email_marketing_config(enabled=True)

    @patch('lms.djangoapps.email_marketing.signals.log.error')
    def test_just_return_signals(self, mock_log_error):
        """
        Ensure that disabling Sailthru just returns
        """
        update_email_marketing_config(enabled=False)

        add_email_marketing_cookies(None)
        self.assertFalse(mock_log_error.called)

        email_marketing_register_user(None, None, None)
        self.assertFalse(mock_log_error.called)

        update_email_marketing_config(enabled=True)

        # test anonymous users
        anon = AnonymousUser()
        email_marketing_register_user(None, anon, None)
        self.assertFalse(mock_log_error.called)

        email_marketing_user_field_changed(None, user=anon)
        self.assertFalse(mock_log_error.called)

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    def test_change_email(self, mock_sailthru):
        """
        test async method in task that changes email in Sailthru
        """
        mock_sailthru.return_value = SailthruResponse(JsonResponse({'ok': True}))
        update_user_email.delay(TEST_EMAIL, "old@edx.org")
        self.assertEqual(mock_sailthru.call_args[0][0], "user")
        userparms = mock_sailthru.call_args[0][1]
        self.assertEqual(userparms['key'], "email")
        self.assertEqual(userparms['id'], "old@edx.org")
        self.assertEqual(userparms['keys']['email'], TEST_EMAIL)

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
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

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list_map_no_list(self, mock_sailthru_client):
        """Test when no list returned from sailthru"""
        mock_sailthru_client.api_get.return_value = SailthruResponse(JsonResponse({'lists': []}))
        self.assertEqual(_get_list_from_email_marketing_provider(mock_sailthru_client), {})
        mock_sailthru_client.api_get.assert_called_with("list", {})

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list_map_error(self, mock_sailthru_client):
        """Test when error occurred while fetching data from sailthru"""
        mock_sailthru_client.api_get.return_value = SailthruResponse(
            JsonResponse({'error': 43, 'errormsg': 'Got an error'})
        )
        self.assertEqual(_get_list_from_email_marketing_provider(mock_sailthru_client), {})

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list_map_exception(self, mock_sailthru_client):
        """Test when exception raised while fetching data from sailthru"""
        mock_sailthru_client.api_get.side_effect = SailthruClientError
        self.assertEqual(_get_list_from_email_marketing_provider(mock_sailthru_client), {})

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_get_sailthru_list(self, mock_sailthru_client):
        """Test fetch list data from sailthru"""
        mock_sailthru_client.api_get.return_value = \
            SailthruResponse(JsonResponse({'lists': [{'name': 'test1_user_list'}]}))
        self.assertEqual(
            _get_list_from_email_marketing_provider(mock_sailthru_client),
            {'test1_user_list': {'name': 'test1_user_list'}}
        )
        mock_sailthru_client.api_get.assert_called_with("list", {})

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_create_sailthru_list(self, mock_sailthru_client):
        """Test create list in sailthru"""
        mock_sailthru_client.api_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        self.assertEqual(_create_user_list(mock_sailthru_client, 'test_list_name'), True)
        self.assertEqual(mock_sailthru_client.api_post.call_args[0][0], "list")
        listparms = mock_sailthru_client.api_post.call_args[0][1]
        self.assertEqual(listparms['list'], 'test_list_name')
        self.assertEqual(listparms['primary'], 0)
        self.assertEqual(listparms['public_name'], 'test_list_name')

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_create_sailthru_list_error(self, mock_sailthru_client):
        """Test error occurrence while creating sailthru list"""
        mock_sailthru_client.api_post.return_value = SailthruResponse(
            JsonResponse({'error': 43, 'errormsg': 'Got an error'})
        )
        self.assertEqual(_create_user_list(mock_sailthru_client, 'test_list_name'), False)

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient')
    def test_create_sailthru_list_exception(self, mock_sailthru_client):
        """Test exception raised while creating sailthru list"""
        mock_sailthru_client.api_post.side_effect = SailthruClientError
        self.assertEqual(_create_user_list(mock_sailthru_client, 'test_list_name'), False)

    @patch('lms.djangoapps.email_marketing.tasks.log.error')
    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
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

    @patch('lms.djangoapps.email_marketing.signals.crum.get_current_request')
    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_register_user(self, mock_update_user, mock_get_current_request):
        """
        make sure register user call invokes update_user and includes activation_key
        """
        mock_get_current_request.return_value = self.request
        email_marketing_register_user(None, user=self.user, registration=self.registration)
        self.assertTrue(mock_update_user.called)
        self.assertEqual(mock_update_user.call_args[0][0]['activation_key'], self.registration.activation_key)
        self.assertLessEqual(mock_update_user.call_args[0][0]['signupNumber'], 9)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_register_user_no_request(self, mock_update_user):
        """
        make sure register user call invokes update_user and includes activation_key
        """
        email_marketing_register_user(None, user=self.user, registration=self.registration)
        self.assertTrue(mock_update_user.called)
        self.assertEqual(mock_update_user.call_args[0][0]['activation_key'], self.registration.activation_key)

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_register_user_language_preference(self, mock_update_user):
        """
        make sure register user call invokes update_user and includes language preference
        """
        # If the user hasn't set an explicit language preference, we should send the application's default.
        self.assertIsNone(self.user.preferences.model.get_value(self.user, LANGUAGE_KEY))
        email_marketing_register_user(None, user=self.user, registration=self.registration)
        self.assertEqual(mock_update_user.call_args[0][0]['ui_lang'], settings.LANGUAGE_CODE)

        # If the user has set an explicit language preference, we should send it.
        self.user.preferences.create(key=LANGUAGE_KEY, value='es-419')
        email_marketing_register_user(None, user=self.user, registration=self.registration)
        self.assertEqual(mock_update_user.call_args[0][0]['ui_lang'], 'es-419')

    @patch.dict(settings.FEATURES, {"ENABLE_THIRD_PARTY_AUTH": False})
    @patch('lms.djangoapps.email_marketing.signals.crum.get_current_request')
    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    @ddt.data(('auth_userprofile', 'gender', 'f', True),
              ('auth_user', 'is_active', 1, True),
              ('auth_userprofile', 'shoe_size', 1, False),
              ('user_api_userpreference', 'pref-lang', 'en', True))
    @ddt.unpack
    def test_modify_field(self, table, setting, value, result, mock_update_user, mock_get_current_request):
        """
        Test that correct fields call update_user
        """
        mock_get_current_request.return_value = self.request
        email_marketing_user_field_changed(None, self.user, table=table, setting=setting, new_value=value)
        self.assertEqual(mock_update_user.called, result)

    @patch('lms.djangoapps.email_marketing.tasks.SailthruClient.api_post')
    @patch('lms.djangoapps.email_marketing.signals.third_party_auth.provider.Registry.get_from_pipeline')
    @patch('lms.djangoapps.email_marketing.signals.third_party_auth.pipeline.get')
    @patch('lms.djangoapps.email_marketing.signals.crum.get_current_request')
    @ddt.data(True, False)
    def test_modify_field_with_sso(self, send_welcome_email, mock_get_current_request,
                                   mock_pipeline_get, mock_registry_get_from_pipeline, mock_sailthru_post):
        """
        Test that welcome email is sent appropriately in the context of SSO registration
        """
        mock_get_current_request.return_value = self.request
        mock_pipeline_get.return_value = 'saml-idp'
        mock_registry_get_from_pipeline.return_value = Mock(send_welcome_email=send_welcome_email)
        mock_sailthru_post.return_value = SailthruResponse(JsonResponse({'ok': True}))
        email_marketing_user_field_changed(None, self.user, table='auth_user', setting='is_active', new_value=True)
        if send_welcome_email:
            self.assertEqual(mock_sailthru_post.call_args[0][0], "send")
        else:
            self.assertNotEqual(mock_sailthru_post.call_args[0][0], "send")

    @patch('lms.djangoapps.email_marketing.tasks.update_user.delay')
    def test_modify_language_preference(self, mock_update_user):
        """
        Test that update_user is called with new language preference
        """
        # If the user hasn't set an explicit language preference, we should send the application's default.
        self.assertIsNone(self.user.preferences.model.get_value(self.user, LANGUAGE_KEY))
        email_marketing_user_field_changed(
            None, self.user, table='user_api_userpreference', setting=LANGUAGE_KEY, new_value=None
        )
        self.assertEqual(mock_update_user.call_args[0][0]['ui_lang'], settings.LANGUAGE_CODE)

        # If the user has set an explicit language preference, we should send it.
        self.user.preferences.create(key=LANGUAGE_KEY, value='fr')
        email_marketing_user_field_changed(
            None, self.user, table='user_api_userpreference', setting=LANGUAGE_KEY, new_value='fr'
        )
        self.assertEqual(mock_update_user.call_args[0][0]['ui_lang'], 'fr')

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


class MockSailthruResponse(object):
    """
    Mock object for SailthruResponse
    """

    def __init__(self, json_response, error=None, code=1):
        self.json = json_response
        self.error = error
        self.code = code

    def is_ok(self):
        """
        Return true of no error
        """
        return self.error is None

    def get_error(self):
        """
        Get error description
        """
        return MockSailthruError(self.error, self.code)


class MockSailthruError(object):
    """
    Mock object for Sailthru Error
    """

    def __init__(self, error, code=1):
        self.error = error
        self.code = code

    def get_message(self):
        """
        Get error description
        """
        return self.error

    def get_error_code(self):
        """
        Get error code
        """
        return self.code


class SailthruTests(TestCase):
    """
    Tests for the Sailthru tasks class.
    """

    def setUp(self):
        super(SailthruTests, self).setUp()
        self.user = UserFactory()
        self.course_id = CourseKey.from_string('edX/toy/2012_Fall')
        self.course_url = 'http://lms.testserver.fake/courses/edX/toy/2012_Fall/info'
        self.course_id2 = 'edX/toy/2016_Fall'
        self.course_url2 = 'http://lms.testserver.fake/courses/edX/toy/2016_Fall/info'

    @patch('sailthru.sailthru_client.SailthruClient.purchase')
    @patch('sailthru.sailthru_client.SailthruClient.api_get')
    @patch('sailthru.sailthru_client.SailthruClient.api_post')
    @patch('edx_toggles.toggles.WaffleSwitchNamespace.is_enabled')
    def test_update_course_enrollment_whitelabel(
            self,
            switch,
            mock_sailthru_api_post,
            mock_sailthru_api_get,
            mock_sailthru_purchase
    ):
        """test user record not sent to sailthru when enrolled in a course at white label site"""
        switch.return_value = True
        white_label_site = Site.objects.create(domain='testwhitelabel.com', name='White Label')
        site_dict = {'id': white_label_site.id, 'domain': white_label_site.domain, 'name': white_label_site.name}
        with patch('lms.djangoapps.email_marketing.signals._get_current_site') as mock_site_info:
            mock_site_info.return_value = site_dict
            update_sailthru(None, self.user, 'audit', str(self.course_id))
            self.assertFalse(mock_sailthru_purchase.called)
            self.assertFalse(mock_sailthru_api_post.called)
            self.assertFalse(mock_sailthru_api_get.called)

    @patch('sailthru.sailthru_client.SailthruClient.purchase')
    def test_switch_is_disabled(self, mock_sailthru_purchase):
        """Make sure sailthru purchase is not called when waffle switch is disabled"""
        update_sailthru(None, self.user, 'verified', self.course_id)
        self.assertFalse(mock_sailthru_purchase.called)

    @patch('edx_toggles.toggles.WaffleSwitchNamespace.is_enabled')
    @patch('sailthru.sailthru_client.SailthruClient.purchase')
    def test_purchase_is_not_invoked(self, mock_sailthru_purchase, switch):
        """Make sure purchase is not called in the following condition:
            i: waffle switch is True and mode is verified
        """
        switch.return_value = True
        update_sailthru(None, self.user, 'verified', self.course_id)
        self.assertFalse(mock_sailthru_purchase.called)

    @patch('edx_toggles.toggles.WaffleSwitchNamespace.is_enabled')
    @patch('sailthru.sailthru_client.SailthruClient.purchase')
    def test_encoding_is_working_for_email_contains_unicode(self, mock_sailthru_purchase, switch):
        """Make sure encoding is working for emails contains unicode characters
        while sending it to sail through.
        """
        switch.return_value = True
        self.user.email = u'tèst@edx.org'
        update_sailthru(None, self.user, 'audit', str(self.course_id))
        self.assertTrue(mock_sailthru_purchase.called)
