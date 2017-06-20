# -*- coding: utf-8 -*-
"""
Utility functions, constants, etc. for testing.
"""

from openedx.core.djangoapps.user_api.accounts import (
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH,
    EMAIL_MAX_LENGTH,
    PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH
)


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
    u'a' * (PASSWORD_MAX_LENGTH + 1)
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
    u'password',  # :)
    u'a' * PASSWORD_MIN_LENGTH,
    u'a' * PASSWORD_MAX_LENGTH
]
