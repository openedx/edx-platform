"""
ACE message types for the verify_student module.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class VerificationExpiry(BaseMessageType):
    APP_LABEL = 'verify_student'
    Name = 'verificationexpiry'

    def __init__(self, *args, **kwargs):
        super(VerificationExpiry, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
