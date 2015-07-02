from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
# TODO PLAT-671 Import from Django 1.8
# from django.utils.translation import LANGUAGE_SESSION_KEY
from django_locale.trans_real import LANGUAGE_SESSION_KEY

from lang_pref.middleware import LanguagePreferenceMiddleware
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from lang_pref import LANGUAGE_KEY
from student.tests.factories import UserFactory


class TestUserPreferenceMiddleware(TestCase):
    """
    Tests to make sure user preferences are getting properly set in the middleware
    """

    def setUp(self):
        super(TestUserPreferenceMiddleware, self).setUp()
        self.middleware = LanguagePreferenceMiddleware()
        self.session_middleware = SessionMiddleware()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/somewhere')
        self.request.user = self.user
        self.session_middleware.process_request(self.request)

    def test_no_language_set_in_session_or_prefs(self):
        # nothing set in the session or the prefs
        self.middleware.process_request(self.request)
        self.assertNotIn(LANGUAGE_SESSION_KEY, self.request.session)

    def test_language_in_user_prefs(self):
        # language set in the user preferences and not the session
        set_user_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)
        self.assertEquals(self.request.session[LANGUAGE_SESSION_KEY], 'eo')

    def test_language_in_session(self):
        # language set in both the user preferences and session,
        # preference should get precedence. The session will hold the last value,
        # which is probably the user's last preference. Look up the updated preference.

        # Dark lang middleware should run after this middleware, so it can
        # set a session language as an override of the user's preference.
        self.request.session[LANGUAGE_SESSION_KEY] = 'en'
        set_user_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)

        self.assertEquals(self.request.session[LANGUAGE_SESSION_KEY], 'eo')
