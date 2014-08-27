from django.test import TestCase
from lang_pref_middleware.tests import LangPrefMiddlewareTestCaseMixin

from lang_pref.middleware import LanguagePreferenceMiddleware
from user_api.models import UserPreference
from lang_pref import LANGUAGE_KEY
from student.tests.factories import UserFactory


class TestUserLanguagePreferenceMiddleware(LangPrefMiddlewareTestCaseMixin, TestCase):
    """
    Tests to make sure user preferences are getting properly set in the middleware
    """
    middleware_class = LanguagePreferenceMiddleware

    def get_user(self):
        return UserFactory.create()

    def set_user_language_preference(self, user, language):
        UserPreference.set_preference(user, LANGUAGE_KEY, language)
