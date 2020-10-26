"""
ACE message types for the student module.
"""

from openedx.core.djangoapps.ace_common.message import BaseMessageType


class PasswordReset(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(PasswordReset, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class AccountRecovery(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(AccountRecovery, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class EmailChange(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(EmailChange, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
