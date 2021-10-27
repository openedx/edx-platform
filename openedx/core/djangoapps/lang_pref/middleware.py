"""
Middleware for Language Preferences
"""


from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation.trans_real import parse_accept_lang_header

from openedx.core.djangoapps.lang_pref import COOKIE_DURATION, LANGUAGE_HEADER, LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration.helpers import get_value
from openedx.core.djangoapps.user_api.errors import UserAPIInternalError, UserAPIRequestError
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference, set_user_preference
from openedx.core.lib.mobile_utils import is_request_from_mobile_app


class LanguagePreferenceMiddleware(MiddlewareMixin):
    """
    Middleware for user preferences.

    Ensures that, once set, a user's preferences are reflected in the page
    whenever they are logged in.
    """

    def process_request(self, request):
        """
        If a user's UserPreference contains a language preference, use the user's preference.
        Save the current language preference cookie as the user's preferred language.

        If site-wide language is set, don't use the language from user's
        preferences and don't set the value from the cookies as the user's
        preffered language.
        Instead use the value set as a site-wide language.
        """
        site_wide_language = get_value('LANGUAGE_CODE', None)
        if site_wide_language:
            request.session[LANGUAGE_SESSION_KEY] = site_wide_language
            self.update_accept_language(request, site_wide_language)
            return

        cookie_lang = request.COOKIES.get(settings.LANGUAGE_COOKIE, None)
        if not cookie_lang:
            return

        if request.user.is_authenticated:
            set_user_preference(request.user, LANGUAGE_KEY, cookie_lang)
        else:
            request._anonymous_user_cookie_lang = cookie_lang  # lint-amnesty, pylint: disable=protected-access

        self.update_accept_language(request, cookie_lang)

        # Allow the new cookie setting to update the language in the user's session
        if LANGUAGE_SESSION_KEY in request.session and request.session[LANGUAGE_SESSION_KEY] != cookie_lang:
            del request.session[LANGUAGE_SESSION_KEY]

    def process_response(self, request, response):  # lint-amnesty, pylint: disable=missing-function-docstring
        site_wide_language = get_value('LANGUAGE_CODE', None)
        if site_wide_language:
            response.set_cookie(
                settings.LANGUAGE_COOKIE,
                value=site_wide_language,
                domain=settings.SESSION_COOKIE_DOMAIN,
                max_age=COOKIE_DURATION,
                secure=request.is_secure()
            )
        else:
            # If the user is logged in, check for their language preference. Also check for real user
            # if current user is a masquerading user,
            user_pref = None
            current_user = None
            if hasattr(request, 'user'):
                current_user = getattr(request.user, 'real_user', request.user)

            if current_user and current_user.is_authenticated:
                anonymous_cookie_lang = getattr(request, '_anonymous_user_cookie_lang', None)
                if anonymous_cookie_lang:
                    user_pref = anonymous_cookie_lang
                    set_user_preference(current_user, LANGUAGE_KEY, anonymous_cookie_lang)
                else:
                    # Get the user's language preference
                    try:
                        user_pref = get_user_preference(current_user, LANGUAGE_KEY)
                    except (UserAPIRequestError, UserAPIInternalError):
                        # If we can't find the user preferences, then don't modify the cookie
                        pass

                # If set, set the user_pref in the LANGUAGE_COOKIE
                if user_pref and not is_request_from_mobile_app(request):
                    response.set_cookie(
                        settings.LANGUAGE_COOKIE,
                        value=user_pref,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        max_age=COOKIE_DURATION,
                        secure=request.is_secure()
                    )
                else:
                    response.delete_cookie(
                        settings.LANGUAGE_COOKIE,
                        domain=settings.SESSION_COOKIE_DOMAIN
                    )

        return response

    def update_accept_language(self, request, new_lang):
        accept_header = request.META.get(LANGUAGE_HEADER, None)
        if accept_header:
            current_langs = parse_accept_lang_header(accept_header)
            # Promote the new_lang over any language currently in the accept header
            current_langs = [(lang, qvalue) for (lang, qvalue) in current_langs if lang != new_lang]
            current_langs.insert(0, (new_lang, 1))
            accept_header = ",".join(f"{lang};q={qvalue}" for (lang, qvalue) in current_langs)
        else:
            accept_header = new_lang
        request.META[LANGUAGE_HEADER] = accept_header
