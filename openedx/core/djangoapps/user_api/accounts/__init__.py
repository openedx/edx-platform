"""
Account constants
"""

# The minimum and maximum length for the name ("full name") account field
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 255

# The minimum and maximum length for the username account field
USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 30

# The minimum and maximum length for the email account field
EMAIL_MIN_LENGTH = 3
EMAIL_MAX_LENGTH = 254

# The minimum and maximum length for the password account field
PASSWORD_MIN_LENGTH = 2
PASSWORD_MAX_LENGTH = 75

ACCOUNT_VISIBILITY_PREF_KEY = 'account_privacy'

# Indicates the user's preference that all users can view the shareable fields in their account information.
ALL_USERS_VISIBILITY = 'all_users'

# Indicates the user's preference that all their account information be private.
PRIVATE_VISIBILITY = 'private'
