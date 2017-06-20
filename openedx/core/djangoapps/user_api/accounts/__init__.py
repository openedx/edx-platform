"""
Account constants
"""

from django.utils.translation import ugettext as _


# The minimum and maximum length for the name ("full name") account field
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 255

# The minimum and maximum length for the username account field
USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 30

# The minimum and maximum length for the email account field
EMAIL_MIN_LENGTH = 3
EMAIL_MAX_LENGTH = 254  # Limit per RFCs is 254

# The minimum and maximum length for the password account field
PASSWORD_MIN_LENGTH = 2
PASSWORD_MAX_LENGTH = 75

ACCOUNT_VISIBILITY_PREF_KEY = 'account_privacy'

# Indicates the user's preference that all users can view the shareable fields in their account information.
ALL_USERS_VISIBILITY = 'all_users'

# Indicates the user's preference that all their account information be private.
PRIVATE_VISIBILITY = 'private'

# Translators: This message is shown when the Unicode usernames are NOT allowed.
# It is shown to users who attempt to create a new account using invalid characters
# in the username.
USERNAME_INVALID_CHARS_ASCII = _(
    u"Usernames can only contain letters (A-Z, a-z), numerals (0-9), underscores (_), and hyphens (-)."
)

# Translators: This message is shown only when the Unicode usernames are allowed.
# It is shown to users who attempt to create a new account using invalid characters
# in the username.
USERNAME_INVALID_CHARS_UNICODE = _(
    u"Usernames can only contain letters, numerals, and @/./+/-/_ characters."
)

# Translators: This message is shown to users who attempt to create a new account using
# an invalid email format.
EMAIL_INVALID_MSG = _(u"Email '{email}' format is not valid")

# Translators: This message is shown to users who attempt to create a new
# account using an username/email associated with an existing account.
EMAIL_CONFLICT_MSG = _(
    u"It looks like {email_address} belongs to an existing account. "
    u"Try again with a different email address."
)
USERNAME_CONFLICT_MSG = _(
    u"It looks like {username} belongs to an existing account. "
    u"Try again with a different username."
)

# Translators: This message is shown to users who enter a username/email/password
# with an inappropriate length (too short or too long).
USERNAME_BAD_LENGTH_MSG = _(u"Username '{username}' must be between {min} and {max} characters long")
EMAIL_BAD_LENGTH_MSG = _(u"Email '{email}' must be between {min} and {max} characters long")
PASSWORD_BAD_LENGTH_MSG = _(u"Password must be between {min} and {max} characters long")

# These strings are normally not user-facing.
USERNAME_BAD_TYPE_MSG = u"Username must be a string"
EMAIL_BAD_TYPE_MSG = u"Email must be a string"
PASSWORD_BAD_TYPE_MSG = u"Password must be a string"

# Translators: This message is shown to users who enter a password matching
# the username they enter(ed).
PASSWORD_CANT_EQUAL_USERNAME_MSG = _(u"Password cannot be the same as the username")
