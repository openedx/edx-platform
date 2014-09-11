"""
Middleware for Language Preferences
"""

from lang_pref_middleware import middleware
from user_api.models import UserPreference
from lang_pref import LANGUAGE_KEY


class LanguagePreferenceMiddleware(middleware.LanguagePreferenceMiddleware):
    def get_user_language_preference(self, user):
        """
        Retrieve the given user's language preference.

        Returns None if no preference set.
        """
        return UserPreference.get_preference(user, LANGUAGE_KEY)
