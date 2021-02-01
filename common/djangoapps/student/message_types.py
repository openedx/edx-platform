"""
ACE message types for the student module.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class AccountRecovery(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options['transactional'] = True


class EmailChange(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options['transactional'] = True


class EmailChangeConfirmation(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options['transactional'] = True


class RecoveryEmailCreate(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options['transactional'] = True


class AccountActivation(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options['transactional'] = True


class ProctoringRequirements(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.options['transactional'] = True
