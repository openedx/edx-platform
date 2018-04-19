"""
This file exposes a number of password complexity validators which can be optionally added to
account creation

This file was inspired by the django-passwords project at https://github.com/dstufft/django-passwords
authored by dstufft (https://github.com/dstufft)
"""
from __future__ import division

import logging
import string
import unicodedata

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy as ungettext
from Levenshtein import distance
from six import text_type

from student.models import PasswordHistory


log = logging.getLogger(__name__)

# In description order
_allowed_password_complexity = [
    'ALPHABETIC',
    'UPPER',
    'LOWER',
    'NUMERIC',
    'DIGITS',
    'PUNCTUATION',
    'NON ASCII',
    'WORDS',
]


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


def password_complexity():
    """
    :return: A dict of complexity requirements from settings
    """
    complexity = {}
    if settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
        complexity = getattr(settings, 'PASSWORD_COMPLEXITY', {})

    valid_complexity = {x: y for x, y in complexity.iteritems() if x in _allowed_password_complexity}

    if not password_complexity.logged:
        invalid = frozenset(complexity.keys()) - frozenset(valid_complexity.keys())
        for key in invalid:
            log.warning('Unrecognized %s value in PASSWORD_COMPLEXITY setting.', key)
        password_complexity.logged = True

    return valid_complexity


# Declare static variable for the function above, which helps avoid issuing multiple log warnings.
# We don't instead keep a cached version of the complexity rules, because that might trip up unit tests.
password_complexity.logged = False


def _password_complexity_descriptions(which=None):
    """
    which: A list of which complexities to describe, None if you want the configured ones
    :return: A list of complexity descriptions
    """
    descs = []
    complexity = password_complexity()
    if which is None:
        which = complexity.keys()

    for key in _allowed_password_complexity:  # we iterate over allowed keys so that we get the order right
        value = complexity.get(key, 0) if key in which else 0
        if not value:
            continue

        if key == 'ALPHABETIC':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} letter', '{num} letters', value).format(num=value))
        elif key == 'UPPER':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} uppercase letter', '{num} uppercase letters', value).format(num=value))
        elif key == 'LOWER':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} lowercase letter', '{num} lowercase letters', value).format(num=value))
        elif key == 'DIGITS':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} digit', '{num} digits', value).format(num=value))
        elif key == 'NUMERIC':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} number', '{num} numbers', value).format(num=value))
        elif key == 'PUNCTUATION':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} punctuation mark', '{num} punctuation marks', value).format(num=value))
        elif key == 'NON ASCII':  # note that our definition of non-ascii is non-letter, non-digit, non-punctuation
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} symbol', '{num} symbols', value).format(num=value))
        elif key == 'WORDS':
            # Translators: This appears in a list of password requirements
            descs.append(ungettext('{num} word', '{num} words', value).format(num=value))
        else:
            raise Exception('Unexpected complexity value {}'.format(key))

    return descs


def password_instructions():
    """
    :return: A string suitable for display to the user to tell them what password to enter
    """
    min_length = password_min_length()
    reqs = _password_complexity_descriptions()

    if not reqs:
        return ungettext('Your password must contain at least {num} character.',
                         'Your password must contain at least {num} characters.',
                         min_length).format(num=min_length)
    else:
        return ungettext('Your password must contain at least {num} character, including {requirements}.',
                         'Your password must contain at least {num} characters, including {requirements}.',
                         min_length).format(num=min_length, requirements=' & '.join(reqs))


def validate_password(password, user=None, username=None, password_reset=True):
    """
    Checks user-provided password against our current site policy.

    Raises a ValidationError or SecurityPolicyError depending on the type of error.

    Arguments:
        password: The user-provided password as a string
        user: A User model object, if available. Required to check against security policy.
        username: The user-provided username, if available. Taken from 'user' if not provided.
        password_reset: Whether to run validators that only make sense in a password reset
         context (like PasswordHistory).
    """
    if not isinstance(password, text_type):
        try:
            password = text_type(password, encoding='utf8')  # some checks rely on unicode semantics (e.g. length)
        except UnicodeDecodeError:
            raise ValidationError(_('Invalid password.'))  # no reason to get into weeds

    username = username or (user and user.username)

    if user and password_reset:
        _validate_password_security(password, user)

    _validate_password_dictionary(password)
    _validate_password_against_username(password, username)

    # Some messages are composable, so we'll add them together here
    errors = [_validate_password_length(password)]
    errors += _validate_password_complexity(password)
    errors = filter(None, errors)

    if errors:
        msg = _('Enter a password with at least {requirements}.').format(requirements=' & '.join(errors))
        raise ValidationError(msg)


def _validate_password_security(password, user):
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


def _validate_password_length(value):
    """
    Validator that enforces minimum length of a password
    """
    min_length = password_min_length()
    max_length = password_max_length()

    if min_length and len(value) < min_length:
        # This is an error that can be composed with other requirements, so just return a fragment
        # Translators: This appears in a list of password requirements
        return ungettext(
            "{num} character",
            "{num} characters",
            min_length
        ).format(num=min_length)
    elif max_length and len(value) > max_length:
        raise ValidationError(ungettext(
            "Enter a password with at most {num} character.",
            "Enter a password with at most {num} characters.",
            max_length
        ).format(num=max_length))


def _validate_password_complexity(value):
    """
    Validator that enforces minimum complexity
    """
    complexities = password_complexity()
    if not complexities:
        return []

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
        errors.append('UPPER')
    if len(lowercase) < complexities.get("LOWER", 0):
        errors.append('LOWER')
    if len(digits) < complexities.get("DIGITS", 0):
        errors.append('DIGITS')
    if len(punctuation) < complexities.get("PUNCTUATION", 0):
        errors.append('PUNCTUATION')
    if len(non_ascii) < complexities.get("NON ASCII", 0):
        errors.append('NON ASCII')
    if len(words) < complexities.get("WORDS", 0):
        errors.append('WORDS')
    if len(numeric) < complexities.get("NUMERIC", 0):
        errors.append('NUMERIC')
    if len(alphabetic) < complexities.get("ALPHABETIC", 0):
        errors.append('ALPHABETIC')

    if errors:
        return _password_complexity_descriptions(errors)
    else:
        return []


def _validate_password_against_username(password, username):
    if not username:
        return

    if password == username:
        # Translators: This message is shown to users who enter a password matching
        # the username they enter(ed).
        raise ValidationError(_(u"Password cannot be the same as the username."))


def _validate_password_dictionary(value):
    """
    Insures that the password is not too similar to a defined set of dictionary words
    """
    if not settings.FEATURES.get('ENFORCE_PASSWORD_POLICY', False):
        return

    password_max_edit_distance = getattr(settings, "PASSWORD_DICTIONARY_EDIT_DISTANCE_THRESHOLD", None)
    password_dictionary = getattr(settings, "PASSWORD_DICTIONARY", None)

    if password_max_edit_distance and password_dictionary:
        for word in password_dictionary:
            edit_distance = distance(value, text_type(word))
            if edit_distance <= password_max_edit_distance:
                raise ValidationError(_("Password is too similar to a dictionary word."),
                                      code="dictionary_word")
