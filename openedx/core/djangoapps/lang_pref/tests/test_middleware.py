"""
Tests for lang_pref middleware.
"""

import mock

from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.translation import LANGUAGE_SESSION_KEY

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.lang_pref.middleware import LanguagePreferenceMiddleware
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference, get_user_preference
from student.tests.factories import UserFactory
from student.tests.factories import AnonymousUserFactory


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

    def test_no_language_set_in_session_or_prefs(self):
        # nothing set in the session or the prefs
        self.middleware.process_request(self.request)
        self.assertNotIn(LANGUAGE_SESSION_KEY, self.request.session)  # pylint: disable=no-member

    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('eo', 'esperanto')])
    )
    def test_language_in_user_prefs(self):
        # language set in the user preferences and not the session
        set_user_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)
        self.assertEquals(self.request.session[LANGUAGE_SESSION_KEY], 'eo')  # pylint: disable=no-member

    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('en', 'english'), ('eo', 'esperanto')])
    )
    def test_language_in_session(self):
        # language set in both the user preferences and session,
        # preference should get precedence. The session will hold the last value,
        # which is probably the user's last preference. Look up the updated preference.

        # Dark lang middleware should run after this middleware, so it can
        # set a session language as an override of the user's preference.
        self.request.session[LANGUAGE_SESSION_KEY] = 'en'  # pylint: disable=no-member
        set_user_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)

        self.assertEquals(self.request.session[LANGUAGE_SESSION_KEY], 'eo')  # pylint: disable=no-member

    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('eo', 'dummy Esperanto'), ('ar', 'arabic')])
    )
    def test_supported_browser_language_in_session(self):
        """
        test: browser language should be set in user session if it is supported by system for unauthenticated user.
        """
        self.request.user = self.anonymous_user
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.session[LANGUAGE_SESSION_KEY], 'ar')   # pylint: disable=no-member

    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('en', 'english')])
    )
    def test_browser_language_not_be_in_session(self):
        """
        test: browser language should not be set in user session if it is not supported by system.
        """
        self.request.user = self.anonymous_user
        self.middleware.process_request(self.request)
        self.assertNotEqual(self.request.session.get(LANGUAGE_SESSION_KEY), 'ar')   # pylint: disable=no-member

    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('en', 'english'), ('ar', 'arabic')])
    )
    def test_delete_user_lang_preference_not_supported_by_system(self):
        """
        test: user preferred language has been removed from user preferences model if it is not supported by system
        for authenticated users.
        """
        set_user_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)
        self.assertEqual(get_user_preference(self.request.user, LANGUAGE_KEY), None)

    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('eu-es', 'euskara (Espainia)'), ('en', 'english')])
    )
    def test_supported_browser_language_prefix_in_session(self):
        """
        test: browser language should be set in user session if it's prefix is supported by system for 
        unathenticated users 
        """
        self.request.META['HTTP_ACCEPT_LANGUAGE'] = 'eu;q=1.0'
        self.request.user = self.anonymous_user
        self.middleware.process_request(self.request)
        self.assertEqual(self.request.session.get(LANGUAGE_SESSION_KEY), 'eu-es')  #pylint: disable=no-member
    
    @mock.patch(
        'openedx.core.djangoapps.lang_pref.middleware.released_languages',
        mock.Mock(return_value=[('en', 'english')])
    )
    def test_unsupported_browser_language_prefix(self):
        """
        test: browser language should not be set in user session if it's prefix is not supported by system.
        """
        self.request.META['HTTP_ACCEPT_LANGUAGE']='eu;q=1.0'
        self.request.user = self.anonymous_user
        self.middleware.process_request(self.request)
        self.assertNotEqual(self.request.session.get(LANGUAGE_SESSION_KEY), 'eu-es')   # pylint: disable=no-member
