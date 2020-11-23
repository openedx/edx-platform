"""
ACE message types for user_authn-related emails.
"""

from openedx.core.djangoapps.ace_common.message import BaseMessageType


class PasswordReset(BaseMessageType):
    """
    A message to the user with password reset link.
    """
    def __init__(self, *args, **kwargs):
        super(PasswordReset, self).__init__(*args, **kwargs)

        # pylint: disable=unsupported-assignment-operation
        self.options['transactional'] = True


class PasswordResetSuccess(BaseMessageType):
    """
    A message to the user when the password rest was successful.
    """

    def __init__(self, *args, **kwargs):
        super(PasswordResetSuccess, self).__init__(*args, **kwargs)
        self.options['transactional'] = True
