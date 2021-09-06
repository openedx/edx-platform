"""
ACE message types for the calendar_sync module.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class CalendarSync(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(CalendarSync, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
