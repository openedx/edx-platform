# -*- coding: utf-8 -*-
"""
Utility functions, constants, etc. for testing.
"""


from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH, USERNAME_MIN_LENGTH
from common.djangoapps.util.password_policy_validators import DEFAULT_MAX_PASSWORD_LENGTH

INVALID_NAMES = [
    None,
    '',
    u''
]

INVALID_USERNAMES_ASCII = [
    '$invalid-ascii$',
    'invalid-fŕáńḱ',
    '@invalid-ascii@'
]

INVALID_USERNAMES_UNICODE = [
    u'invalid-unicode_fŕáńḱ',
]

INVALID_USERNAMES = [
    None,
    u'',
    u'a',
    u'a' * (USERNAME_MAX_LENGTH + 1),
] + INVALID_USERNAMES_ASCII + INVALID_USERNAMES_UNICODE

INVALID_EMAILS = [
    None,
    u'',
    u'a',
    'no_domain',
    'no+domain',
    '@',
    '@domain.com',
    'test@no_extension',
    u'fŕáńḱ@example.com',

    # Long email -- subtract the length of the @domain
    # except for one character (so we exceed the max length limit)
    u'{user}@example.com'.format(
        user=(u'e' * (EMAIL_MAX_LENGTH - 11))
    )
]

INVALID_PASSWORDS = [
    None,
    u'',
    u'a',
    u'a' * (DEFAULT_MAX_PASSWORD_LENGTH + 1),
]

INVALID_COUNTRIES = [
    None,
    "",
    "--"
]

VALID_NAMES = [
    'Validation Bot',
    u'Validation Bot'
]

VALID_USERNAMES_UNICODE = [
    u'Enchanté',
    u'username_with_@',
    u'username with spaces',
    u'eastern_arabic_numbers_١٢٣',
]

VALID_USERNAMES = [
    u'username',
    u'a' * USERNAME_MIN_LENGTH,
    u'a' * USERNAME_MAX_LENGTH,
    u'-' * USERNAME_MIN_LENGTH,
    u'-' * USERNAME_MAX_LENGTH,
    u'_username_',
    u'-username-',
    u'-_username_-'
]

VALID_EMAILS = [
    'has@domain.com'
]

VALID_PASSWORDS = [
    u'good_password_339',
]

VALID_COUNTRIES = [
    u'PK',
    u'Pakistan',
    u'US'
]
