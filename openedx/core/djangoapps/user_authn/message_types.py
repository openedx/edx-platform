"""
ACE message types for user_authn-related emails.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class PasswordReset(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(PasswordReset, self).__init__(*args, **kwargs)

        # pylint: disable=unsupported-assignment-operation
        self.options['transactional'] = True
