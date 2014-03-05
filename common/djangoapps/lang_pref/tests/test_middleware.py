from django.test import TestCase
from django.test.client import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from lang_pref.middleware import LanguagePreferenceMiddleware
from user_api.models import UserPreference
from lang_pref import LANGUAGE_KEY
from student.tests.factories import UserFactory


class TestUserPreferenceMiddleware(TestCase):
    """
    Tests to make sure user preferences are getting properly set in the middleware
    """

    def setUp(self):
        self.middleware = LanguagePreferenceMiddleware()
        self.session_middleware = SessionMiddleware()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/somewhere')
        self.request.user = self.user
        self.session_middleware.process_request(self.request)

    def test_no_language_set_in_session_or_prefs(self):
        # nothing set in the session or the prefs
        self.middleware.process_request(self.request)
        self.assertNotIn('django_language', self.request.session)

    def test_language_in_user_prefs(self):
        # language set in the user preferences and not the session
        UserPreference.set_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)
        self.assertEquals(self.request.session['django_language'], 'eo')

    def test_language_in_session(self):
        # language set in both the user preferences and session,
        # session should get precedence
        self.request.session['django_language'] = 'en'
        UserPreference.set_preference(self.user, LANGUAGE_KEY, 'eo')
        self.middleware.process_request(self.request)

        self.assertEquals(self.request.session['django_language'], 'en')
