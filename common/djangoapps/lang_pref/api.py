# -*- coding: utf-8 -*-
""" Python API for language and translation management. """

from collections import namedtuple

from django.conf import settings
from django.utils.translation import ugettext as _
from dark_lang.models import DarkLangConfig


# Named tuples can be referenced using object-like variable
# deferencing, making the use of tuples more readable by
# eliminating the need to see the context of the tuple packing.
Language = namedtuple('Language', 'code name')


def released_languages():
    """Retrieve the list of released languages.

    Constructs a list of Language tuples by intersecting the
    list of valid language tuples with the list of released
    language codes.

    Returns:
       list of Language: Languages in which full translations are available.

    Example:

        >>> print released_languages()
        [Language(code='en', name=u'English'), Language(code='fr', name=u'Français')]

    """
    released_language_codes = DarkLangConfig.current().released_languages_list
    default_language_code = settings.LANGUAGE_CODE

    if default_language_code not in released_language_codes:
        released_language_codes.append(default_language_code)
        released_language_codes.sort()

    # Intersect the list of valid language tuples with the list
    # of release language codes
    released_languages = [
        Language(tuple[0], tuple[1])
        for tuple in settings.LANGUAGES
        if tuple[0] in released_language_codes
    ]

    return released_languages


def all_languages():
    """Retrieve the list of all languages, translated and sorted.

    Returns:
        list of (language code (str), language name (str)): the language names
        are translated in the current activated language and the results sorted
        alphabetically.

    """
    languages = [(lang[0], _(lang[1])) for lang in settings.ALL_LANGUAGES]  # pylint: disable=translation-of-non-string
    return sorted(languages, key=lambda lang: lang[1])
