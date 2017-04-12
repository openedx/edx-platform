"""
Tests for lang_pref middleware.
"""

import itertools
import mock

import ddt
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.http import HttpResponse
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import parse_accept_lang_header

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY, LANGUAGE_COOKIE, COOKIE_DURATION
from openedx.core.djangoapps.lang_pref.middleware import LanguagePreferenceMiddleware
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, get_user_preference, delete_user_preference
from student.tests.factories import UserFactory
from student.tests.factories import AnonymousUserFactory


@ddt.ddt
class TestUserPreferenceMiddleware(TestCase):
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
        self.request.META['HTTP_ACCEPT_LANGUAGE'] = 'ar;q=1.0'  # pylint: disable=no-member
        self.session_middleware.process_request(self.request)

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
                LANGUAGE_COOKIE,
                value=lang_pref_out,
                domain=settings.SESSION_COOKIE_DOMAIN,
                max_age=COOKIE_DURATION,
            )
        else:
            response.delete_cookie.assert_called_with(
                LANGUAGE_COOKIE,
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
        self.request.COOKIES[LANGUAGE_COOKIE] = lang_cookie

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
            # (LANGUAGE_COOKIE, LANGUAGE_SESSION_KEY, Accept-Language In, Accept-Language Out)
            (None, None, None, None),
            (None, 'eo', None, None),
            (None, 'eo', 'en', 'en'),
            (None, None, 'en', 'en'),
            ('en', None, None, 'en'),
            ('en', None, 'eo', 'en;q=1.0,eo'),
            ('en', None, 'en', 'en'),
            ('en', 'eo', 'en', 'en'),
            ('en', 'eo', 'eo', 'en;q=1.0,eo')
        ]
    ))
    @ddt.unpack
    def test_preference_cookie_overrides_browser(self, logged_in, lang_cookie, lang_session, accept_lang_in, accept_lang_out):
        if not logged_in:
            self.request.user = self.anonymous_user
        if lang_cookie:
            self.request.COOKIES[LANGUAGE_COOKIE] = lang_cookie
        if lang_session:
            self.request.session[LANGUAGE_SESSION_KEY] = lang_session
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
            self.assertItemsEqual(accept_lang_result, accept_lang_out)
        else:
            self.assertEqual(accept_lang_result, accept_lang_out)

        self.assertEquals(self.request.session.get(LANGUAGE_SESSION_KEY), lang_session)

    def test_process_response_no_user_noop(self):
        del self.request.user
        response = mock.Mock(spec=HttpResponse)

        result = self.middleware.process_response(self.request, response)

        self.assertIs(result, response)
        self.assertEqual(response.mock_calls, [])
