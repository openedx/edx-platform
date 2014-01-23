"""
Middleware for dark-launching languages. These languages won't be used
when determining which translation to give a user based on their browser
header, but can be selected by setting the ``preview-lang`` query parameter
to the language code.

Adding the query parameter ``clear-lang`` will reset the language stored
in the user's session.

This middleware must be placed before the LocaleMiddleware, but after
the SessionMiddleware.
"""

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.translation.trans_real import parse_accept_lang_header


class DarkLangMiddleware(object):
    """
    Middleware for dark-launching languages.

    This middleware will only be active if the RELEASED_LANGUAGES setting is set.
    This setting should contain a list of language codes for languages which
    are considered to be dark-launched, and those won't activate based on a
    users browser settings.
    """

    def __init__(self):
        self.released_langs = getattr(settings, 'RELEASED_LANGUAGES', None)

        if self.released_langs is None:
            raise MiddlewareNotUsed()

    def process_request(self, request):
        self._clean_accept_headers(request)
        self._activate_preview_language(request)

    def _is_released(self, lang_code):
        """
        ``True`` iff one of the values in ``self.released_langs`` is a prefix of ``lang_code``.
        """
        return any(lang_code.startswith(released_lang) for released_lang in self.released_langs)

    def _format_accept_value(self, lang, priority=1.0):
        """
        Formats lang and priority into a valid accept header fragment.
        """
        return "{};q={}".format(lang, priority)

    def _clean_accept_headers(self, request):
        """
        Remove any language that is not either in ``self.released_langs`` or
        a territory of one of those languages.
        """
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', None)
        if accept is None or accept == '*':
            return

        new_accept = ", ".join(
            self._format_accept_value(lang, priority)
            for lang, priority
            in parse_accept_lang_header(accept)
            if self._is_released(lang)
        )

        request.META['HTTP_ACCEPT_LANGUAGE'] = new_accept

    def _activate_preview_language(self, request):
        """
        If the request has the get parameter ``preview-lang``,
        and that language appears doesn't appear in ``self.released_langs``,
        then set the session ``django_language`` to that language.
        """
        if 'clear-lang' in request.GET:
            if 'django_language' in request.session:
                del request.session['django_language']

        preview_lang = request.GET.get('preview-lang', None)

        if not preview_lang:
            return

        if preview_lang in self.released_langs:
            return

        request.session['django_language'] = preview_lang
