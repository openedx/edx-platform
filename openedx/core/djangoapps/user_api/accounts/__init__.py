"""
Account constants
"""


from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

# The maximum length for the bio ("about me") account field
BIO_MAX_LENGTH = 300

# The minimum and maximum length for the name ("full name") account field
NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 255

# The minimum and maximum length for the username account field
USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 30

# The minimum and maximum length for the email account field
EMAIL_MIN_LENGTH = 3
EMAIL_MAX_LENGTH = 254  # Limit per RFCs is 254

ACCOUNT_VISIBILITY_PREF_KEY = 'account_privacy'

# Indicates the user's preference that all users can view the shareable fields in their account information.
ALL_USERS_VISIBILITY = 'all_users'

# Indicates the user's preference that all their account information be private.
PRIVATE_VISIBILITY = 'private'

# Indicates that the user has custom preferences for the visibility of their account information.
CUSTOM_VISIBILITY = 'custom'

# Prefix prepended to user preferences related to custom account visibility preferences.
VISIBILITY_PREFIX = 'visibility.'

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
EMAIL_INVALID_MSG = _(u'"{email}" is not a valid email address.')

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
USERNAME_BAD_LENGTH_MSG = format_lazy(
    _(u"Username must be between {min} and {max} characters long."),
    min=USERNAME_MIN_LENGTH,
    max=USERNAME_MAX_LENGTH,
)
EMAIL_BAD_LENGTH_MSG = format_lazy(
    _(u"Enter a valid email address that contains at least {min} characters."),
    min=EMAIL_MIN_LENGTH,
)

# These strings are normally not user-facing.
USERNAME_BAD_TYPE_MSG = u"Username must be a string."
EMAIL_BAD_TYPE_MSG = u"Email must be a string."
PASSWORD_BAD_TYPE_MSG = u"Password must be a string."

# Translators: These messages are shown to users who do not enter information
# into the required field or enter it incorrectly.
REQUIRED_FIELD_NAME_MSG = _(u"Enter your full name.")
REQUIRED_FIELD_CONFIRM_EMAIL_MSG = _(u"The email addresses do not match.")
REQUIRED_FIELD_COUNTRY_MSG = _(u"Select your country or region of residence.")
REQUIRED_FIELD_PROFESSION_SELECT_MSG = _(u"Select your profession.")
REQUIRED_FIELD_SPECIALTY_SELECT_MSG = _(u"Select your specialty.")
REQUIRED_FIELD_PROFESSION_TEXT_MSG = _(u"Enter your profession.")
REQUIRED_FIELD_SPECIALTY_TEXT_MSG = _(u"Enter your specialty.")
REQUIRED_FIELD_CITY_MSG = _(u"Enter your city.")
REQUIRED_FIELD_GOALS_MSG = _(u"Tell us your goals.")
REQUIRED_FIELD_LEVEL_OF_EDUCATION_MSG = _(u"Select the highest level of education you have completed.")
REQUIRED_FIELD_MAILING_ADDRESS_MSG = _(u"Enter your mailing address.")
