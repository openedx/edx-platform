"""
Middleware for Language Preferences
"""

from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from lang_pref import LANGUAGE_KEY
# TODO PLAT-671 Import from Django 1.8
# from django.utils.translation import LANGUAGE_SESSION_KEY
from django_locale.trans_real import LANGUAGE_SESSION_KEY


class LanguagePreferenceMiddleware(object):
    """
    Middleware for user preferences.

    Ensures that, once set, a user's preferences are reflected in the page
    whenever they are logged in.
    """

    def process_request(self, request):
        """
        If a user's UserPreference contains a language preference, use the user's preference.
        """
        # If the user is logged in, check for their language preference
        if request.user.is_authenticated():
            # Get the user's language preference
            user_pref = get_user_preference(request.user, LANGUAGE_KEY)
            # Set it to the LANGUAGE_SESSION_KEY (Django-specific session setting governing language pref)
            if user_pref:
                request.session[LANGUAGE_SESSION_KEY] = user_pref
