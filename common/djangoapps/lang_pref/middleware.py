"""
Middleware for Language Preferences
"""

from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
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
        # If the user is logged in, check for their language preference
        if request.user.is_authenticated():
            # Get the user's language preference
            user_pref = get_user_preference(request.user, LANGUAGE_KEY)
            # Set it to the LANGUAGE_SESSION_KEY (Django-specific session setting governing language pref)
            if user_pref:
                request.session[LANGUAGE_SESSION_KEY] = user_pref
            else:
                # Setting the session language to the browser language, if it is supported.
                preferred_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
                lang_headers = [seq[0] for seq in parse_accept_lang_header(preferred_language)]
                languages = released_languages()
                for browser_lang in lang_headers:
                    if browser_lang in [seq[0] for seq in languages]:
                        if request.session.get(LANGUAGE_SESSION_KEY, None) != browser_lang:
                            request.session[LANGUAGE_SESSION_KEY] = unicode(browser_lang)
                        break
