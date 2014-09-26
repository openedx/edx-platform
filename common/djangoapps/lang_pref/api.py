# -*- coding: utf-8 -*-
""" Python API for language and translation management. """

from collections import namedtuple

from django.conf import settings
from django.utils.translation import get_language
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


def preferred_language(preferred_language_code):
    """Retrieve the name of the user's preferred language.

    Note:
        The preferred_language_code may be None. If this is the case,
        the if/else block will handle it by returning either the active
        language or the default language.

    Args:
        preferred_language_code (str): The ISO 639 code corresponding
            to the user's preferred language.

    Returns:
       unicode: The name of the user's preferred language.

    """
    active_language_code = get_language()

    if preferred_language_code in settings.LANGUAGE_DICT:
        # If the user has indicated a preference for a valid
        # language, record their preferred language
        preferred_language = settings.LANGUAGE_DICT[preferred_language_code]
    elif active_language_code in settings.LANGUAGE_DICT:
        # Otherwise, set the language used in the current thread
        # as the preferred language
        preferred_language = settings.LANGUAGE_DICT[active_language_code]
    else:
        # Otherwise, use the default language
        preferred_language = settings.LANGUAGE_DICT[settings.LANGUAGE_CODE]

    return preferred_language
