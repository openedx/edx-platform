"""
Middleware for Language Preferences
"""

from openedx.core.djangoapps.user_api.preferences.api import get_user_preference, delete_user_preference
from lang_pref import LANGUAGE_KEY
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import parse_accept_lang_header
from lang_pref.api import released_languages


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
        languages = released_languages()
        system_released_languages = [seq[0] for seq in languages]

        # If the user is logged in, check for their language preference
        if request.user.is_authenticated():
            # Get the user's language preference
            user_pref = get_user_preference(request.user, LANGUAGE_KEY)
            # Set it to the LANGUAGE_SESSION_KEY (Django-specific session setting governing language pref)
            if user_pref:
                if user_pref in system_released_languages:
                    request.session[LANGUAGE_SESSION_KEY] = user_pref
                else:
                    delete_user_preference(request.user, LANGUAGE_KEY)
        else:
            preferred_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            lang_headers = [seq[0] for seq in parse_accept_lang_header(preferred_language)]

            # Setting the session language to the browser language, if it is supported.
            for browser_lang in lang_headers:
                if browser_lang in system_released_languages:
                    if request.session.get(LANGUAGE_SESSION_KEY, None) is None:
                        request.session[LANGUAGE_SESSION_KEY] = unicode(browser_lang)
                    break
