"""
This file exposes a number of password complexity validators which can be optionally added to
account creation

This file was inspired by the django-passwords project at https://github.com/dstufft/django-passwords
authored by dstufft (https://github.com/dstufft)
"""
from __future__ import division

import string
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy as ungettext
from Levenshtein import distance
from six import text_type

from student.models import PasswordHistory


class SecurityPolicyError(ValidationError):
    pass


def password_min_length():
    """
    Returns minimum required length of a password.
    Can be overridden by site configuration of PASSWORD_MIN_LENGTH.
    """
    min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', None)
    if min_length is None:
        return 2  # Note: This default is simply historical
    return min_length


def password_max_length():
    """
    Returns maximum allowed length of a password. If zero, no maximum.
    Can be overridden by site configuration of PASSWORD_MAX_LENGTH.
    """
    # Note: The default value here is simply historical
    max_length = getattr(settings, 'PASSWORD_MAX_LENGTH', None)
    if max_length is None:
        return 75  # Note: This default is simply historical
    return max_length


def validate_password(password, user=None, username=None):
    """
    Checks user-provided password against our current site policy.

    Raises a ValidationError or SecurityPolicyError depending on the type of error.

    Arguments:
        password: The user-provided password as a string
        user: A User model object, if available. Required to check against security policy.
        username: The user-provided username, if available. Taken from 'user' if not provided.
    """
    username = username or (user and user.username)

    if user:
        validate_password_security(password, user)

    validate_password_length(password)

    if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
        validate_password_complexity(password)
        validate_password_dictionary(password)

    if username:
        validate_password_against_username(password, username)


def validate_password_security(password, user):
    """
    Check password reuse and similar operational security policy considerations.
    """
    # Check reuse
    if not PasswordHistory.is_allowable_password_reuse(user, password):
        if user.is_staff:
            num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STAFF_PASSWORDS_BEFORE_REUSE']
        else:
            num_distinct = settings.ADVANCED_SECURITY_CONFIG['MIN_DIFFERENT_STUDENT_PASSWORDS_BEFORE_REUSE']
        raise SecurityPolicyError(ungettext(
            "You are re-using a password that you have used recently. "
            "You must have {num} distinct password before reusing a previous password.",
            "You are re-using a password that you have used recently. "
            "You must have {num} distinct passwords before reusing a previous password.",
            num_distinct
        ).format(num=num_distinct))

    # Check reset frequency
    if PasswordHistory.is_password_reset_too_soon(user):
        num_days = settings.ADVANCED_SECURITY_CONFIG['MIN_TIME_IN_DAYS_BETWEEN_ALLOWED_RESETS']
        raise SecurityPolicyError(ungettext(
            "You are resetting passwords too frequently. Due to security policies, "
            "{num} day must elapse between password resets.",
            "You are resetting passwords too frequently. Due to security policies, "
            "{num} days must elapse between password resets.",
            num_days
        ).format(num=num_days))


def validate_password_length(value):
    """
    Validator that enforces minimum length of a password
    """
    message = _("Password: Invalid Length ({0})")
    code = "length"

    min_length = password_min_length()
    max_length = password_max_length()

    if min_length and len(value) < min_length:
        raise ValidationError(message.format(_("must be {0} characters or more").format(min_length)), code=code)
    elif max_length and len(value) > max_length:
        raise ValidationError(message.format(_("must be {0} characters or fewer").format(max_length)), code=code)


def validate_password_complexity(value):
    """
    Validator that enforces minimum complexity
    """
    message = _("Password: Must be more complex ({0})")
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


def validate_password_against_username(password, username):
    if password == username:
        # Translators: This message is shown to users who enter a password matching
        # the username they enter(ed).
        raise ValidationError(_(u"Password cannot be the same as the username"))


def validate_password_dictionary(value):
    """
    Insures that the password is not too similar to a defined set of dictionary words
    """
    password_max_edit_distance = getattr(settings, "PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD", None)
    password_dictionary = getattr(settings, "PASSWORD_DICTIONARY", None)

    if password_max_edit_distance and password_dictionary:
        for word in password_dictionary:
            edit_distance = distance(text_type(value), text_type(word))
            if edit_distance <= password_max_edit_distance:
                raise ValidationError(_("Password: Too similar to a restricted dictionary word."),
                                      code="dictionary_word")
