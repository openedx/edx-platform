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

from django.utils.translation.trans_real import parse_accept_lang_header

from dark_lang.models import DarkLangConfig


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
        return DarkLangConfig.current().released_languages_list

    def process_request(self, request):
        """
        Prevent user from requesting un-released languages except by using the preview-lang query string.
        """
        if not DarkLangConfig.current().enabled:
            return

        self._clean_accept_headers(request)
        self._activate_preview_language(request)

    def _is_released(self, lang_code):
        """
        ``True`` iff one of the values in ``self.released_langs`` is a prefix of ``lang_code``.
        """
        return any(lang_code.lower().startswith(released_lang.lower()) for released_lang in self.released_langs)

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
        and that language doesn't appear in ``self.released_langs``,
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
