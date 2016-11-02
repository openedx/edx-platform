# pylint: disable=no-member
# pylint: disable=protected-access
"""
Unit tests for SafeSessionMiddleware
"""
import ddt
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse, HttpResponseRedirect, SimpleCookie
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch
from nose.plugins.attrib import attr

from openedx.core.djangolib.testing.utils import get_mock_request

from student.tests.factories import UserFactory

from ..middleware import SafeSessionMiddleware, SafeCookieData
from .test_utils import TestSafeSessionsLogMixin, 


create_mock_request = get_mock_request


@attr(shard=2)
class TestSafeSessionProcessRequest(TestSafeSessionsLogMixin, TestCase):
    """
    Test class for SafeSessionMiddleware.process_request
    """
    def setUp(self):
        super(TestSafeSessionProcessRequest, self).setUp()
        self.user = UserFactory.create()
        self.request = create_mock_request()

    def assert_response(self, safe_cookie_data=None, success=True):
        """
        Calls SafeSessionMiddleware.process_request and verifies
        the response.

        Arguments:
            safe_cookie_data - If provided, it is serialized and
              stored in the request's cookies.
            success - If True, verifies a successful response.
              Else, verifies a failed response with an HTTP redirect.
        """
        if safe_cookie_data:
            self.request.COOKIES[settings.SESSION_COOKIE_NAME] = unicode(safe_cookie_data)
        response = SafeSessionMiddleware().process_request(self.request)
        if success:
            self.assertIsNone(response)
            self.assertIsNone(getattr(self.request, 'need_to_delete_cookie', None))
        else:
            self.assertEquals(response.status_code, HttpResponseRedirect.status_code)
            self.assertTrue(self.request.need_to_delete_cookie)

    def assert_no_session(self):
        """
        Asserts that a session object is *not* set on the request.
        """
        self.assertIsNone(getattr(self.request, 'session', None))

    def assert_no_user_in_session(self):
        """
        Asserts that a user object is *not* set on the request's session.
        """
        self.assertIsNone(self.request.session.get(SESSION_KEY))

    def assert_user_in_session(self):
        """
        Asserts that a user object *is* set on the request's session.
        """
        self.assertEquals(
            SafeSessionMiddleware.get_user_id_from_session(self.request),
            self.user.id
        )

    def test_success(self):
        self.client.login(username=self.user.username, password='test')
        session_id = self.client.session.session_key
        safe_cookie_data = SafeCookieData.create(session_id, self.user.id)

        # pre-verify steps 3, 4, 5
        self.assertIsNone(getattr(self.request, 'session', None))
        self.assertIsNone(getattr(self.request, 'safe_cookie_verified_user_id', None))

        # verify step 1: safe cookie data is parsed
        self.assert_response(safe_cookie_data)
        self.assert_user_in_session()

        # verify step 2: cookie value is replaced with parsed session_id
        self.assertEquals(self.request.COOKIES[settings.SESSION_COOKIE_NAME], session_id)

        # verify step 3: session set in request
        self.assertIsNotNone(self.request.session)

        # verify steps 4, 5: user_id stored for later verification
        self.assertEquals(self.request.safe_cookie_verified_user_id, self.user.id)

    def test_success_no_cookies(self):
        self.assert_response()
        self.assert_no_user_in_session()

    def test_success_no_session(self):
        safe_cookie_data = SafeCookieData.create('no_such_session_id', self.user.id)
        self.assert_response(safe_cookie_data)
        self.assert_no_user_in_session()

    def test_success_no_session_and_user(self):
        safe_cookie_data = SafeCookieData.create('no_such_session_id', 'no_such_user')
        self.assert_response(safe_cookie_data)
        self.assert_no_user_in_session()

    def test_parse_error_at_step_1(self):
        with self.assert_parse_error():
            self.assert_response('not-a-safe-cookie', success=False)
        self.assert_no_session()

    def test_invalid_user_at_step_4(self):
        self.client.login(username=self.user.username, password='test')
        safe_cookie_data = SafeCookieData.create(self.client.session.session_key, 'no_such_user')
        with self.assert_incorrect_user_logged():
            self.assert_response(safe_cookie_data, success=False)
        self.assert_user_in_session()


@attr(shard=2)
@ddt.ddt
class TestSafeSessionProcessResponse(TestSafeSessionsLogMixin, TestCase):
    """
    Test class for SafeSessionMiddleware.process_response
    """
    def setUp(self):
        super(TestSafeSessionProcessResponse, self).setUp()
        self.user = UserFactory.create()
        self.request = create_mock_request()
        self.request.session = {}
        self.client.response = HttpResponse()
        self.client.response.cookies = SimpleCookie()

    def assert_response(self, set_request_user=False, set_session_cookie=False):
        """
        Calls SafeSessionMiddleware.process_response and verifies
        the response.

        Arguments:
            set_request_user - If True, the user is set on the request
                object.
            set_session_cookie - If True, a session_id is set in the
                session cookie in the response.
        """
        if set_request_user:
            self.request.user = self.user
            SafeSessionMiddleware.set_user_id_in_session(self.request, self.user)
        if set_session_cookie:
            self.client.response.cookies[settings.SESSION_COOKIE_NAME] = "some_session_id"

        response = SafeSessionMiddleware().process_response(self.request, self.client.response)
        self.assertEquals(response.status_code, 200)

    def assert_response_with_delete_cookie(
            self,
            expect_delete_called=True,
            set_request_user=False,
            set_session_cookie=False,
    ):
        """
        Calls SafeSessionMiddleware.process_response and verifies
        the response, while expecting the cookie to be deleted if
        expect_delete_called is True.

        See assert_response for information on the other
        parameters.
        """
        with patch('django.http.HttpResponse.set_cookie') as mock_delete_cookie:
            self.assert_response(set_request_user=set_request_user, set_session_cookie=set_session_cookie)
            self.assertEquals(mock_delete_cookie.called, expect_delete_called)

    def test_success(self):
        with self.assert_not_logged():
            self.assert_response(set_request_user=True, set_session_cookie=True)

    def test_confirm_user_at_step_2(self):
        self.request.safe_cookie_verified_user_id = self.user.id
        with self.assert_not_logged():
            self.assert_response(set_request_user=True, set_session_cookie=True)

    def test_different_user_at_step_2_error(self):
        self.request.safe_cookie_verified_user_id = "different_user"

        with self.assert_logged_for_request_user_mismatch("different_user", self.user.id, 'warning'):
            self.assert_response(set_request_user=True, set_session_cookie=True)

        with self.assert_logged_for_session_user_mismatch("different_user", self.user.id):
            self.assert_response(set_request_user=True, set_session_cookie=True)

    def test_anonymous_user(self):
        self.request.safe_cookie_verified_user_id = self.user.id
        self.request.user = AnonymousUser()
        self.request.session[SESSION_KEY] = self.user.id
        with self.assert_no_error_logged():
            with self.assert_logged_for_request_user_mismatch(self.user.id, None, 'debug'):
                self.assert_response(set_request_user=False, set_session_cookie=True)

    def test_update_cookie_data_at_step_3(self):
        self.assert_response(set_request_user=True, set_session_cookie=True)

        serialized_cookie_data = self.client.response.cookies[settings.SESSION_COOKIE_NAME].value
        safe_cookie_data = SafeCookieData.parse(serialized_cookie_data)
        self.assertEquals(safe_cookie_data.version, SafeCookieData.CURRENT_VERSION)
        self.assertEquals(safe_cookie_data.session_id, "some_session_id")
        self.assertTrue(safe_cookie_data.verify(self.user.id))

    def test_cant_update_cookie_at_step_3_error(self):
        self.client.response.cookies[settings.SESSION_COOKIE_NAME] = None
        with self.assert_invalid_session_id():
            self.assert_response_with_delete_cookie(set_request_user=True)

    @ddt.data(True, False)
    def test_deletion_of_cookies_at_step_4(self, set_request_user):
        self.request.need_to_delete_cookie = True
        self.assert_response_with_delete_cookie(set_session_cookie=True, set_request_user=set_request_user)

    def test_deletion_of_no_cookies_at_step_4(self):
        self.request.need_to_delete_cookie = True
        # delete_cookies is called even if there are no cookies set
        self.assert_response_with_delete_cookie()


@attr(shard=2)
@ddt.ddt
class TestSafeSessionMiddleware(TestSafeSessionsLogMixin, TestCase):
    """
    Test class for SafeSessionMiddleware, testing both
    process_request and process_response.
    """
    def setUp(self):
        super(TestSafeSessionMiddleware, self).setUp()
        self.user = UserFactory.create()
        self.request = create_mock_request()
        self.client.response = HttpResponse()
        self.client.response.cookies = SimpleCookie()

    def cookies_from_request_to_response(self):
        """
        Transfers the cookies from the request object to the response
        object.
        """
        if self.request.COOKIES.get(settings.SESSION_COOKIE_NAME):
            self.client.response.cookies[settings.SESSION_COOKIE_NAME] = self.request.COOKIES[
                settings.SESSION_COOKIE_NAME
            ]

    def verify_success(self):
        """
        Verifies success path.
        """
        self.client.login(username=self.user.username, password='test')
        self.request.user = self.user

        session_id = self.client.session.session_key
        safe_cookie_data = SafeCookieData.create(session_id, self.user.id)
        self.request.COOKIES[settings.SESSION_COOKIE_NAME] = unicode(safe_cookie_data)

        with self.assert_not_logged():
            response = SafeSessionMiddleware().process_request(self.request)
        self.assertIsNone(response)

        self.assertEquals(self.request.safe_cookie_verified_user_id, self.user.id)
        self.cookies_from_request_to_response()

        with self.assert_not_logged():
            response = SafeSessionMiddleware().process_response(self.request, self.client.response)
        self.assertEquals(response.status_code, 200)

    def test_success(self):
        self.verify_success()

    def test_success_from_mobile_web_view(self):
        self.request.path = '/xblock/block-v1:org+course+run+type@html+block@block_id'
        self.verify_success()

    @override_settings(MOBILE_APP_USER_AGENT_REGEXES=[r'open edX Mobile App'])
    def test_success_from_mobile_app(self):
        self.request.META = {'HTTP_USER_AGENT': 'open edX Mobile App Version 2.1'}
        self.verify_success()

    def verify_error(self, expected_response_status):
        """
        Verifies error path.
        """
        self.request.COOKIES[settings.SESSION_COOKIE_NAME] = 'not-a-safe-cookie'

        with self.assert_parse_error():
            request_response = SafeSessionMiddleware().process_request(self.request)
            self.assertEquals(request_response.status_code, expected_response_status)

        self.assertTrue(self.request.need_to_delete_cookie)
        self.cookies_from_request_to_response()

        with patch('django.http.HttpResponse.set_cookie') as mock_delete_cookie:
            SafeSessionMiddleware().process_response(self.request, self.client.response)
            self.assertTrue(mock_delete_cookie.called)

    def test_error(self):
        self.verify_error(302)

    def test_error_from_mobile_web_view(self):
        self.request.path = '/xblock/block-v1:org+course+run+type@html+block@block_id'
        self.verify_error(401)

    @override_settings(MOBILE_APP_USER_AGENT_REGEXES=[r'open edX Mobile App'])
    def test_error_from_mobile_app(self):
        self.request.META = {'HTTP_USER_AGENT': 'open edX Mobile App Version 2.1'}
        self.verify_error(401)
