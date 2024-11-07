"""
ACE message types for support-related emails.
"""

from openedx.core.djangoapps.ace_common.message import BaseMessageType


class WholeCourseReset(BaseMessageType):
    """
    A message to the user when whole course reset was successful.
    """

    APP_LABEL = 'support'
    Name = 'wholecoursereset'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options['transactional'] = True
