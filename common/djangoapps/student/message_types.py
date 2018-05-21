"""
ACE message types for the student module.
"""
from django.conf import settings

from edx_ace.message import MessageType
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class PasswordReset(MessageType):
    def __init__(self, *args, **kwargs):
        super(PasswordReset, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
        self.options['from_address'] = configuration_helpers.get_value(
            'email_from_address', settings.DEFAULT_FROM_EMAIL
        )
