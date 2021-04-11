"""
Tests for lang_pref middleware.
"""


import itertools

import ddt
import mock
import six
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test.client import Client, RequestFactory
from django.urls import reverse
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import parse_accept_lang_header
from openedx.core.djangoapps.lang_pref import COOKIE_DURATION, LANGUAGE_KEY
from openedx.core.djangoapps.lang_pref.middleware import LanguagePreferenceMiddleware
from openedx.core.djangoapps.user_api.preferences.api import (
    delete_user_preference,
    get_user_preference,
    set_user_preference
)
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory


@ddt.ddt
class TestUserPreferenceMiddleware(CacheIsolationTestCase):
    """
    Tests to make sure user preferences are getting properly set in the middleware.
    """

    def setUp(self):
        super(TestUserPreferenceMiddleware, self).setUp()
        self.middleware = LanguagePreferenceMiddleware()
        self.session_middleware = SessionMiddleware()
        self.user = UserFactory.create()
        self.anonymous_user = AnonymousUserFactory()
        self.request = RequestFactory().get('/somewhere')
        self.request.user = self.user
        self.request.META['HTTP_ACCEPT_LANGUAGE'] = 'ar;q=1.0'
        self.session_middleware.process_request(self.request)
        self.client = Client()

    def test_logout_shouldnt_remove_cookie(self):

        self.middleware.process_request(self.request)

        self.request.user = self.anonymous_user

        response = mock.Mock(spec=HttpResponse)
        self.middleware.process_response(self.request, response)

        response.delete_cookie.assert_not_called()

    @ddt.data(None, 'es', 'en')
    def test_preference_setting_changes_cookie(self, lang_pref_out):
        """
        Test that the LANGUAGE_COOKIE is always set to the user's current language preferences
        at the end of the request, with an expiry that's the same as the users current session cookie.
        """
        if lang_pref_out:
            set_user_preference(self.user, LANGUAGE_KEY, lang_pref_out)
        else:
            delete_user_preference(self.user, LANGUAGE_KEY)

        response = mock.Mock(spec=HttpResponse)
        self.middleware.process_response(self.request, response)

        if lang_pref_out:
            response.set_cookie.assert_called_with(
                settings.LANGUAGE_COOKIE,
                value=lang_pref_out,
                domain=settings.SESSION_COOKIE_DOMAIN,
                max_age=COOKIE_DURATION,
                secure=self.request.is_secure(),
            )
        else:
            response.delete_cookie.assert_called_with(
                settings.LANGUAGE_COOKIE,
                domain=settings.SESSION_COOKIE_DOMAIN,
            )

        self.assertNotIn(LANGUAGE_SESSION_KEY, self.request.session)

    @ddt.data(*itertools.product(
        (None, 'eo', 'es'),  # LANGUAGE_COOKIE
        (None, 'es', 'en'),  # Language Preference In
    ))
    @ddt.unpack
    @mock.patch('openedx.core.djangoapps.lang_pref.middleware.set_user_preference')
    def test_preference_cookie_changes_setting(self, lang_cookie, lang_pref_in, mock_set_user_preference):
        self.request.COOKIES[settings.LANGUAGE_COOKIE] = lang_cookie

        if lang_pref_in:
            set_user_preference(self.user, LANGUAGE_KEY, lang_pref_in)
        else:
            delete_user_preference(self.user, LANGUAGE_KEY)

        self.middleware.process_request(self.request)

        if lang_cookie is None:
            self.assertEqual(mock_set_user_preference.mock_calls, [])
        else:
            mock_set_user_preference.assert_called_with(self.user, LANGUAGE_KEY, lang_cookie)

    @ddt.data(*(
        (logged_in, ) + test_def
        for logged_in in (True, False)
        for test_def in [
            # (LANGUAGE_COOKIE, LANGUAGE_SESSION_KEY, Accept-Language In,
            #  Accept-Language Out, Session Lang Out)
            (None, None, None, None, None),
            (None, 'eo', None, None, 'eo'),
            (None, 'en', None, None, 'en'),
            (None, 'eo', 'en', 'en', 'eo'),
            (None, None, 'en', 'en', None),
            ('en', None, None, 'en', None),
            ('en', 'en', None, 'en', 'en'),
            ('en', None, 'eo', 'en;q=1.0,eo', None),
            ('en', None, 'en', 'en', None),
            ('en', 'eo', 'en', 'en', None),
            ('en', 'eo', 'eo', 'en;q=1.0,eo', None)
        ]
    ))
    @ddt.unpack
    def test_preference_cookie_overrides_browser(
            self, logged_in, lang_cookie, lang_session_in, accept_lang_in, accept_lang_out,
            lang_session_out,
    ):
        if not logged_in:
            self.request.user = self.anonymous_user
        if lang_cookie:
            self.request.COOKIES[settings.LANGUAGE_COOKIE] = lang_cookie
        if lang_session_in:
            self.request.session[LANGUAGE_SESSION_KEY] = lang_session_in
        if accept_lang_in:
            self.request.META['HTTP_ACCEPT_LANGUAGE'] = accept_lang_in
        else:
            del self.request.META['HTTP_ACCEPT_LANGUAGE']

        self.middleware.process_request(self.request)

        accept_lang_result = self.request.META.get('HTTP_ACCEPT_LANGUAGE')
        if accept_lang_result:
            accept_lang_result = parse_accept_lang_header(accept_lang_result)

        if accept_lang_out:
            accept_lang_out = parse_accept_lang_header(accept_lang_out)

        if accept_lang_out and accept_lang_result:
            six.assertCountEqual(self, accept_lang_result, accept_lang_out)
        else:
            self.assertEqual(accept_lang_result, accept_lang_out)

        self.assertEqual(self.request.session.get(LANGUAGE_SESSION_KEY), lang_session_out)

    @ddt.data(None, 'es', 'en')
    def test_logout_preserves_cookie(self, lang_cookie):
        if lang_cookie:
            self.client.cookies[settings.LANGUAGE_COOKIE] = lang_cookie
        elif settings.LANGUAGE_COOKIE in self.client.cookies:
            del self.client.cookies[settings.LANGUAGE_COOKIE]
        # Use an actual call to the logout endpoint, because the logout function
        # explicitly clears all cookies
        self.client.get(reverse('logout'))
        if lang_cookie:
            self.assertEqual(
                self.client.cookies[settings.LANGUAGE_COOKIE].value,
                lang_cookie
            )
        else:
            self.assertNotIn(settings.LANGUAGE_COOKIE, self.client.cookies)

    @ddt.data(
        (None, None),
        ('es', 'es-419'),
        ('en', 'en'),
        ('es-419', 'es-419')
    )
    @ddt.unpack
    def test_login_captures_lang_pref(self, lang_cookie, expected_lang):
        if lang_cookie:
            self.client.cookies[settings.LANGUAGE_COOKIE] = lang_cookie
        elif settings.LANGUAGE_COOKIE in self.client.cookies:
            del self.client.cookies[settings.LANGUAGE_COOKIE]

        # Use an actual call to the login endpoint, to validate that the middleware
        # stack does the right thing
        response = self.client.post(
            reverse('user_api_login_session'),
            data={
                'email': self.user.email,
                'password': UserFactory._DEFAULT_PASSWORD,  # pylint: disable=protected-access
                'remember': True,
            }
        )

        self.assertEqual(response.status_code, 200)

        if lang_cookie:
            self.assertEqual(response['Content-Language'], expected_lang)
            self.assertEqual(get_user_preference(self.user, LANGUAGE_KEY), lang_cookie)
            self.assertEqual(
                self.client.cookies[settings.LANGUAGE_COOKIE].value,
                lang_cookie
            )
        else:
            self.assertEqual(response['Content-Language'], 'en')
            self.assertEqual(get_user_preference(self.user, LANGUAGE_KEY), None)
            self.assertEqual(self.client.cookies[settings.LANGUAGE_COOKIE].value, '')

    def test_process_response_no_user_noop(self):
        del self.request.user
        response = mock.Mock(spec=HttpResponse)

        result = self.middleware.process_response(self.request, response)

        self.assertIs(result, response)
        self.assertEqual(response.mock_calls, [])

    def test_preference_update_noop(self):
        self.request.COOKIES[settings.LANGUAGE_COOKIE] = 'es'

        # No preference yet, should write to the database

        self.assertEqual(get_user_preference(self.user, LANGUAGE_KEY), None)
        self.middleware.process_request(self.request)
        self.assertEqual(get_user_preference(self.user, LANGUAGE_KEY), 'es')

        response = mock.Mock(spec=HttpResponse)

        with self.assertNumQueries(1):
            self.middleware.process_response(self.request, response)

        # Preference is the same as the cookie, shouldn't write to the database

        with self.assertNumQueries(3):
            self.middleware.process_request(self.request)

        self.assertEqual(get_user_preference(self.user, LANGUAGE_KEY), 'es')

        response = mock.Mock(spec=HttpResponse)

        with self.assertNumQueries(1):
            self.middleware.process_response(self.request, response)

        # Cookie changed, should write to the database again

        self.request.COOKIES[settings.LANGUAGE_COOKIE] = 'en'
        self.middleware.process_request(self.request)
        self.assertEqual(get_user_preference(self.user, LANGUAGE_KEY), 'en')

        with self.assertNumQueries(1):
            self.middleware.process_response(self.request, response)

    @mock.patch('openedx.core.djangoapps.lang_pref.middleware.is_request_from_mobile_app')
    @mock.patch('openedx.core.djangoapps.lang_pref.middleware.get_user_preference')
    def test_remove_lang_cookie_for_mobile_app(self, mock_get_user_preference, mock_is_mobile_request):
        """
        Test to verify language preference cookie removed for mobile app requests.
        """
        mock_get_user_preference.return_value = 'en'
        mock_is_mobile_request.return_value = False
        response = mock.Mock(spec=HttpResponse)

        response = self.middleware.process_response(self.request, response)
        response.delete_cookie.assert_not_called()
        response.set_cookie.assert_called()

        mock_is_mobile_request.return_value = True
        response = self.middleware.process_response(self.request, response)
        response.delete_cookie.assert_called()
