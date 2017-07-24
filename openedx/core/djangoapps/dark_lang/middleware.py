"""
Middleware for dark-launching languages. These languages won't be used
when determining which translation to give a user based on their browser
header, but can be selected by setting the Preview Languages on the Dark
Language setting page.

This middleware must be placed before the LocaleMiddleware, but after
the SessionMiddleware.
"""
from django.conf import settings
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import ugettext as _
from django.utils.translation.trans_real import parse_accept_lang_header

from openedx.core.djangoapps.dark_lang import DARK_LANGUAGE_KEY
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import (
    delete_user_preference,
    get_user_preference,
    set_user_preference
)
from openedx.core.djangoapps.util.user_messages import (
    register_error_message,
    register_success_message,
)

# If django 1.7 or higher is used, the right-side can be updated with new-style codes.
CHINESE_LANGUAGE_CODE_MAP = {
    # The following are the new-style language codes for chinese language
    'zh-hans': 'zh-CN',  # Chinese (Simplified),
    'zh-hans-cn': 'zh-CN',  # Chinese (Simplified, China)
    'zh-hans-sg': 'zh-CN',  # Chinese (Simplified, Singapore)
    'zh-hant': 'zh-TW',  # Chinese (Traditional)
    'zh-hant-hk': 'zh-HK',  # Chinese (Traditional, Hongkong)
    'zh-hant-mo': 'zh-TW',  # Chinese (Traditional, Macau)
    'zh-hant-tw': 'zh-TW',  # Chinese (Traditional, Taiwan)
    # The following are the old-style language codes that django does not recognize
    'zh-mo': 'zh-TW',  # Chinese (Traditional, Macau)
    'zh-sg': 'zh-CN',  # Chinese (Simplified, Singapore)
}

LANGUAGE_INPUT_FIELD = 'preview_lang'


def _dark_parse_accept_lang_header(accept):
    """
    The use of 'zh-cn' for 'Simplified Chinese' and 'zh-tw' for 'Traditional Chinese'
    are now deprecated, as discussed here: https://code.djangoproject.com/ticket/18419.
    The new language codes 'zh-hans' and 'zh-hant' are now used since django 1.7.
    Although majority of browsers still use the old language codes, some new browsers
    such as IE11 in Windows 8.1 start to use the new ones, which makes the current
    chinese translations of edX don't work properly under these browsers.
    This function can keep compatibility between the old and new language codes. If one
    day edX uses django 1.7 or higher, this function can be modified to support the old
    language codes until there are no browsers use them.
    """
    browser_langs = parse_accept_lang_header(accept)
    django_langs = []
    for lang, priority in browser_langs:
        lang = CHINESE_LANGUAGE_CODE_MAP.get(lang.lower(), lang)
        django_langs.append((lang, priority))

    return django_langs


class DarkLangMiddleware(object):
    """
    Middleware for dark-launching languages.

    This is configured by creating ``DarkLangConfig`` rows in the database,
    using the django admin site.
    """
    @property
    def released_langs(self):
        """
        Current list of released languages
        """
        language_options = DarkLangConfig.current().released_languages_list
        if settings.LANGUAGE_CODE not in language_options:
            language_options.append(settings.LANGUAGE_CODE)
        return language_options

    def process_request(self, request):
        """
        Prevent user from requesting un-released languages except by using the preview-lang query string.
        """
        if not DarkLangConfig.current().enabled:
            return

        self._clean_accept_headers(request)
        self._activate_preview_language(request)

    def _fuzzy_match(self, lang_code):
        """Returns a fuzzy match for lang_code"""
        match = None
        if lang_code in self.released_langs:
            match = lang_code
        else:
            lang_prefix = lang_code.partition('-')[0]
            for released_lang in self.released_langs:
                released_prefix = released_lang.partition('-')[0]
                if lang_prefix == released_prefix:
                    match = released_lang
        return match

    def _clean_accept_headers(self, request):
        """
        Remove any language that is not either in ``self.released_langs`` or
        a territory of one of those languages.
        """
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', None)
        if accept is None or accept == '*':
            return

        new_accept = []
        for lang, priority in _dark_parse_accept_lang_header(accept):
            fuzzy_code = self._fuzzy_match(lang.lower())
            if fuzzy_code:
                # Formats lang and priority into a valid accept header fragment.
                new_accept.append("{};q={}".format(fuzzy_code, priority))

        new_accept = ", ".join(new_accept)

        request.META['HTTP_ACCEPT_LANGUAGE'] = new_accept

    def _activate_preview_language(self, request):
        """
        Check the user's dark language setting in the session and apply it
        """
        auth_user = request.user.is_authenticated()

        if auth_user:
            # If this is a post, process a preview language update if requested
            if request.method == 'POST':
                self.process_darklang_request(request)

            # Get the request user's dark lang preference
            preview_lang = get_user_preference(request.user, DARK_LANGUAGE_KEY)

            # Set the session key to the requested preview lang, if set
            if preview_lang:
                request.session[LANGUAGE_SESSION_KEY] = preview_lang

    def process_darklang_request(self, request):
        """
        Proccess the request to set or clear the DarkLang depending on the incoming request.

        Arguments:
            request (Request): The Django Request Object

        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        if not DarkLangConfig.current().enabled:
            return

        if 'set_preview_lang' in request.POST:
            # Set the Preview Language
            self._set_preview_language(request)
        elif 'reset_preview_lang' in request.POST:
            # Reset and clear the language preference
            self._clear_preview_language(request)

    def _set_preview_language(self, request):
        """
        Set the Preview language

        Arguments:
            request (Request): The incoming Django Request
            context dict: The basic context for the Response

        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        preview_lang = request.POST.get(LANGUAGE_INPUT_FIELD, '')
        if not preview_lang.strip():
            register_error_message(request, _('Language code not provided'))
        else:
            # Set the session key to the requested preview lang
            request.session[LANGUAGE_SESSION_KEY] = preview_lang

            # Make sure that we set the requested preview lang as the dark lang preference for the
            # user, so that the lang_pref middleware doesn't clobber away the dark lang preview.
            auth_user = request.user
            if auth_user:
                set_user_preference(request.user, DARK_LANGUAGE_KEY, preview_lang)

            register_success_message(
                request,
                _('Language set to language code: {preview_language_code}').format(
                    preview_language_code=preview_lang
                )
            )

    def _clear_preview_language(self, request):
        """
        Clears the dark language preview

        Arguments:
            request (Request): The incoming Django Request
            context dict: The basic context for the Response
        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        # delete the session language key (if one is set)
        if LANGUAGE_SESSION_KEY in request.session:
            del request.session[LANGUAGE_SESSION_KEY]

        user_pref = ''
        auth_user = request.user
        if auth_user:
            # Reset user's dark lang preference to null
            delete_user_preference(auth_user, DARK_LANGUAGE_KEY)
            # Get & set user's preferred language
            user_pref = get_user_preference(auth_user, LANGUAGE_KEY)
            if user_pref:
                request.session[LANGUAGE_SESSION_KEY] = user_pref
        if user_pref is None:
            register_success_message(request, _('Language reset to the default language code'))
        else:
            register_success_message(
                request,
                _("Language reset to user's preference: {preview_language_code}").format(
                    preview_language_code=user_pref
                )
            )
