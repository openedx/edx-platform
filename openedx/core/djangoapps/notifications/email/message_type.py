"""
Email notifications MessageType
"""
from django.conf import settings
from edx_ace.message import MessageType


class EmailNotificationMessageType(MessageType):
    """
    Edx-ace MessageType for Email Notifications
    """

    NAME = "notifications"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options['transactional'] = True
        self.options['from_address'] = settings.NOTIFICATIONS_DEFAULT_FROM_EMAIL
        self.options['skip_disable_user_policy'] = True
