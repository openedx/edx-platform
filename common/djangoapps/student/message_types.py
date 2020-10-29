"""
ACE message types for the student module.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class AccountRecovery(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(AccountRecovery, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class EmailChange(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(EmailChange, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class EmailChangeConfirmation(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(EmailChangeConfirmation, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class RecoveryEmailCreate(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(RecoveryEmailCreate, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class AccountActivation(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(AccountActivation, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
