"""
ACE message types for the subscriptions module.
"""
from openedx.core.djangoapps.ace_common.message import BaseMessageType


class ImpendingExpiryNotification(BaseMessageType):
    """
    ACE notification message for subscriptions with impending expiry.
    """
    APP_LABEL = 'subscriptions'
    Name = 'impendingexpiry'

    def __init__(self, *args, **kwargs):
        super(ImpendingExpiryNotification, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class ExpiredNotification(BaseMessageType):
    """
    ACE notification message for expired subscriptions.
    """
    APP_LABEL = 'subscriptions'
    Name = 'expired'

    def __init__(self, *args, **kwargs):
        super(ExpiredNotification, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
