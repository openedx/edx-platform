"""
This file exposes a number of password complexity validators which can be optionally added to
account creation

This file was inspired by the django-passwords project at https://github.com/dstufft/django-passwords
authored by dstufft (https://github.com/dstufft)
"""
from __future__ import division
import string

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import nltk


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
    min_password_complexity_score = getattr(settings, "MINIMUM_PASSWORD_COMPLEXITY_SCORE", 0)

    if complexities is None:
        return

    uppercase, lowercase, digits, non_ascii, punctuation = [], [], [], [], []

    for character in value:
        if character.isupper():
            uppercase.append(character)
        elif character.islower():
            lowercase.append(character)
        elif character.isdigit():
            digits.append(character)
        elif character in string.punctuation:
            punctuation.append(character)
        else:
            non_ascii.append(character)

    words = value.split()
    password_complexity_score = 0

    errors = []

    if len(uppercase) < complexities.get("UPPER", 0):
        errors.append((_("must contain {0} or more uppercase characters").format(complexities["UPPER"]), complexities.get("UPPER_SCORE", 1)))
    elif complexities.get("UPPER", 0) > 0:
        password_complexity_score += complexities.get("UPPER_SCORE", 1)

    if len(lowercase) < complexities.get("LOWER", 0):
        errors.append((_("must contain {0} or more lowercase characters").format(complexities["LOWER"]), complexities.get("LOWER_SCORE", 1)))
    elif complexities.get("LOWER", 0) > 0:
        password_complexity_score += complexities.get("LOWER_SCORE", 1)

    if len(digits) < complexities.get("DIGITS", 0):
        errors.append((_("must contain {0} or more digits").format(complexities["DIGITS"]), complexities.get("DIGITS_SCORE", 2)))
    elif complexities.get("DIGITS", 0) > 0:
        password_complexity_score += complexities.get("DIGITS_SCORE", 2)

    if len(punctuation) < complexities.get("PUNCTUATION", 0):
        errors.append((_("must contain {0} or more punctuation characters").format(complexities["PUNCTUATION"]), complexities.get("PUNCTUATION_SCORE", 2)))
    elif complexities.get("PUNCTUATION", 0) > 0:
        password_complexity_score += complexities.get("PUNCTUATION_SCORE", 2)

    if len(non_ascii) < complexities.get("NON ASCII", 0):
        errors.append((_("must contain {0} or more non ascii characters").format(complexities["NON ASCII"]), complexities.get("NON_ASCII_SCORE", 2)))
    elif complexities.get("NON ASCII", 0) > 0:
        password_complexity_score += complexities.get("NON_ASCII_SCORE", 2)

    if len(words) < complexities.get("WORDS", 0):
        errors.append((_("must contain {0} or more unique words").format(complexities["WORDS"]), complexities.get("WORDS_SCORE", 2)))
    elif complexities.get("WORDS", 0) > 0:
        password_complexity_score += complexities.get("WORDS_SCORE", 2)

    if 0 < min_password_complexity_score <= password_complexity_score:
        return
    if errors:
        #show only those errors required to achieve minimum password complexity score
        diff = min_password_complexity_score - password_complexity_score
        if diff > 0:
            filtered_error_messages = get_filtered_messages(diff, errors)
            raise ValidationError(message.format(u', '.join(filtered_error_messages)), code=code)
        else:
            raise ValidationError(message.format(u', '.join(error[0] for error in errors)), code=code)


def get_filtered_messages(diff, errors):
    """
    Get Filtered error Messages for password complexity
    """
    from operator import itemgetter
    weight = 0
    # sort the array
    sorted_errors = sorted(errors, key=itemgetter(1))
    error_messages = []
    index = 0
    while diff > weight and len(sorted_errors) > index:
        error_messages.append(sorted_errors[index][0])
        weight += sorted_errors[index][1]
        index += 1
    return error_messages


def validate_password_dictionary(value):
    """
    Insures that the password is not too similar to a defined set of dictionary words
    """
    password_max_edit_distance = getattr(settings, "PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD", None)
    password_dictionary = getattr(settings, "PASSWORD_DICTIONARY", None)

    if password_max_edit_distance and password_dictionary:
        for word in password_dictionary:
            distance = nltk.metrics.distance.edit_distance(value, word)
            if distance <= password_max_edit_distance:
                raise ValidationError(_("Too similar to a restricted dictionary word."), code="dictionary_word")
