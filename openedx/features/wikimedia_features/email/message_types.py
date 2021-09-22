from openedx.core.djangoapps.ace_common.message import BaseMessageType


class PendingMessagesNotification(BaseMessageType):
    """
    A message for notifying users about pending messages.
    """
    APP_LABEL = 'messenger'
