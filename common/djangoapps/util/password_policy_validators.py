"""
This file exposes a number of password complexity validators which can be optionally added to
account creation

This file was inspired by the django-passwords project at https://github.com/dstufft/django-passwords
authored by dstufft (https://github.com/dstufft)
"""
from __future__ import division

import string
import unicodedata

from nltk.metrics.distance import edit_distance
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_password_strength(value):
    """
    This function loops through each validator defined in this file
    and applies it to a user's proposed password

    Args:
        value: a user's proposed password

    Returns: None, but raises a ValidationError if the proposed password
        fails any one of the validators in password_validators
    """
    password_validators = [
        validate_password_length,
        validate_password_complexity,
        validate_password_dictionary,
    ]
    for validator in password_validators:
        validator(value)


def validate_password_length(value):
    """
    Validator that enforces minimum length of a password
    """
    message = _("Invalid Length ({0})")
    code = "length"

    min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', None)
    max_length = getattr(settings, 'PASSWORD_MAX_LENGTH', None)

    if min_length and len(value) < min_length:
        raise ValidationError(message.format(_("must be {0} characters or more").format(min_length)), code=code)
    elif max_length and len(value) > max_length:
        raise ValidationError(message.format(_("must be {0} characters or fewer").format(max_length)), code=code)


def validate_password_complexity(value):
    """
    Validator that enforces minimum complexity
    """
    message = _("Must be more complex ({0})")
    code = "complexity"

    complexities = getattr(settings, "PASSWORD_COMPLEXITY", None)

    if complexities is None:
        return

    # Sets are here intentionally
    uppercase, lowercase, digits, non_ascii, punctuation = set(), set(), set(), set(), set()
    alphabetic, numeric = [], []

    for character in value:
        if character.isupper():
            uppercase.add(character)
        elif character.islower():
            lowercase.add(character)
        elif character.isdigit():
            digits.add(character)
        elif character in string.punctuation:
            punctuation.add(character)
        else:
            non_ascii.add(character)

        if character.isalpha():
            alphabetic.append(character)
        if 'N' in unicodedata.category(character):  # Check to see if the unicode category contains a 'N'umber
            numeric.append(character)

    words = set(value.split())

    errors = []
    if len(uppercase) < complexities.get("UPPER", 0):
        errors.append(_("must contain {0} or more uppercase characters").format(complexities["UPPER"]))
    if len(lowercase) < complexities.get("LOWER", 0):
        errors.append(_("must contain {0} or more lowercase characters").format(complexities["LOWER"]))
    if len(digits) < complexities.get("DIGITS", 0):
        errors.append(_("must contain {0} or more digits").format(complexities["DIGITS"]))
    if len(punctuation) < complexities.get("PUNCTUATION", 0):
        errors.append(_("must contain {0} or more punctuation characters").format(complexities["PUNCTUATION"]))
    if len(non_ascii) < complexities.get("NON ASCII", 0):
        errors.append(_("must contain {0} or more non ascii characters").format(complexities["NON ASCII"]))
    if len(words) < complexities.get("WORDS", 0):
        errors.append(_("must contain {0} or more unique words").format(complexities["WORDS"]))
    if len(numeric) < complexities.get("NUMERIC", 0):
        errors.append(_("must contain {0} or more numbers").format(complexities["NUMERIC"]))
    if len(alphabetic) < complexities.get("ALPHABETIC", 0):
        errors.append(_("must contain {0} or more letters").format(complexities["ALPHABETIC"]))

    if errors:
        raise ValidationError(message.format(u', '.join(errors)), code=code)


def validate_password_dictionary(value):
    """
    Insures that the password is not too similar to a defined set of dictionary words
    """
    password_max_edit_distance = getattr(settings, "PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD", None)
    password_dictionary = getattr(settings, "PASSWORD_DICTIONARY", None)

    if password_max_edit_distance and password_dictionary:
        for word in password_dictionary:
            distance = edit_distance(value, word)
            if distance <= password_max_edit_distance:
                raise ValidationError(_("Too similar to a restricted dictionary word."), code="dictionary_word")
