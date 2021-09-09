"""
Django Signal related functionality for user_api accounts
"""


from django.dispatch import Signal

# Signal to retire a user from LMS-initiated mailings (course mailings, etc)
USER_RETIRE_MAILINGS = Signal()

# Signal to retire LMS critical information
USER_RETIRE_LMS_CRITICAL = Signal()

# Signal to retire LMS misc information
USER_RETIRE_LMS_MISC = Signal()
