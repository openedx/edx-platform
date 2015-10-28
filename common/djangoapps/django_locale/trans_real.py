"""Translation helper functions."""
# Imported from Django 1.8
# pylint: disable=invalid-name
import re
from django.conf import settings
from django.conf.locale import LANG_INFO
from django.utils import translation


# Format of Accept-Language header values. From RFC 2616, section 14.4 and 3.9.
# and RFC 3066, section 2.1
accept_language_re = re.compile(r'''
    ([A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})*|\*)         # "en", "en-au", "x-y-z", "*"
    (?:\s*;\s*q=(0(?:\.\d{,3})?|1(?:.0{,3})?))?   # Optional "q=1.00", "q=0.8"
    (?:\s*,\s*|$)                                 # Multiple accepts per header.
    ''', re.VERBOSE)


language_code_re = re.compile(r'^[a-z]{1,8}(?:-[a-z0-9]{1,8})*$', re.IGNORECASE)


LANGUAGE_SESSION_KEY = '_language'


def parse_accept_lang_header(lang_string):
    """
    Parses the lang_string, which is the body of an HTTP Accept-Language
    header, and returns a list of (lang, q-value), ordered by 'q' values.

    Any format errors in lang_string results in an empty list being returned.
    """
    # parse_accept_lang_header is broken until we are on Django 1.5 or greater
    # See https://code.djangoproject.com/ticket/19381
    result = []
    pieces = accept_language_re.split(lang_string)
    if pieces[-1]:
        return []
    for i in range(0, len(pieces) - 1, 3):
        first, lang, priority = pieces[i: i + 3]
        if first:
            return []
        priority = priority and float(priority) or 1.0
        result.append((lang, priority))
    result.sort(key=lambda k: k[1], reverse=True)
    return result


def get_supported_language_variant(lang_code, strict=False):
    """
    Returns the language-code that's listed in supported languages, possibly
    selecting a more generic variant. Raises LookupError if nothing found.
    If `strict` is False (the default), the function will look for an alternative
    country-specific variant when the currently checked is not found.
    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.
    """
    if lang_code:
        # If 'fr-ca' is not supported, try special fallback or language-only 'fr'.
        possible_lang_codes = [lang_code]
        try:
            # TODO skip this, or import updated LANG_INFO format from __future__
            # (fallback option wasn't added until
            # https://github.com/django/django/commit/5dcdbe95c749d36072f527e120a8cb463199ae0d)
            possible_lang_codes.extend(LANG_INFO[lang_code]['fallback'])
        except KeyError:
            pass
        generic_lang_code = lang_code.split('-')[0]
        possible_lang_codes.append(generic_lang_code)
        supported_lang_codes = dict(settings.LANGUAGES)

        for code in possible_lang_codes:
            # Note: django 1.4 implementation of check_for_language is OK to use
            if code in supported_lang_codes and translation.check_for_language(code):
                return code
        if not strict:
            # if fr-fr is not supported, try fr-ca.
            for supported_code in supported_lang_codes:
                if supported_code.startswith(generic_lang_code + '-'):
                    return supported_code
    raise LookupError(lang_code)


def get_language_from_request(request, check_path=False):
    """
    Analyzes the request to find what language the user wants the system to
    show. Only languages listed in settings.LANGUAGES are taken into account.
    If the user requests a sublanguage where we have a main language, we send
    out the main language.
    If check_path is True, the URL path prefix will be checked for a language
    code, otherwise this is skipped for backwards compatibility.
    """
    if check_path:
        # Note: django 1.4 implementation of get_language_from_path is OK to use
        lang_code = translation.get_language_from_path(request.path_info)
        if lang_code is not None:
            return lang_code

    supported_lang_codes = dict(settings.LANGUAGES)

    if hasattr(request, 'session'):
        lang_code = request.session.get(LANGUAGE_SESSION_KEY)
        # Note: django 1.4 implementation of check_for_language is OK to use
        if lang_code in supported_lang_codes and lang_code is not None and translation.check_for_language(lang_code):
            return lang_code

    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    try:
        return get_supported_language_variant(lang_code)
    except LookupError:
        pass

    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    # broken in 1.4, so defined above
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == '*':
            break

        if not language_code_re.search(accept_lang):
            continue

        try:
            return get_supported_language_variant(accept_lang)
        except LookupError:
            continue

    try:
        return get_supported_language_variant(settings.LANGUAGE_CODE)
    except LookupError:
        return settings.LANGUAGE_CODE
