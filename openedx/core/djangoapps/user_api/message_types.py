"""
Message Types for user_api emails
"""

from django.conf import settings

from edx_ace import message
from openedx.core.djangoapps.site_configuration import helpers


class DeletionNotificationMessage(message.MessageType):
    """
    Message to notify learners that their account is queued for deletion.
    """
    def __init__(self, *args, **kwargs):
        super(DeletionNotificationMessage, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
        self.options['from_address'] = helpers.get_value(
            'email_from_address', settings.DEFAULT_FROM_EMAIL
        )
