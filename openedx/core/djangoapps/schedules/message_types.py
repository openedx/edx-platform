"""
ACE message types for the schedules module.
"""

import logging

from openedx.core.djangoapps.ace_common.message import BaseMessageType
from openedx.core.djangoapps.schedules.config import DEBUG_MESSAGE_WAFFLE_FLAG


class ScheduleMessageType(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_level = logging.DEBUG if DEBUG_MESSAGE_WAFFLE_FLAG.is_enabled() else None
        self.options['override_frequency_capping'] = True


class RecurringNudge(ScheduleMessageType):
    def __init__(self, day, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = f"recurringnudge_day{day}"


class UpgradeReminder(ScheduleMessageType):
    pass


class CourseUpdate(ScheduleMessageType):
    pass


class InstructorLedCourseUpdate(ScheduleMessageType):
    pass
