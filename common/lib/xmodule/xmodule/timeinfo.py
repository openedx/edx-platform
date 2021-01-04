

import logging

import six
from xmodule.fields import Timedelta

log = logging.getLogger(__name__)


class TimeInfo(object):
    """
    This is a simple object that calculates and stores datetime information for an XModule
    based on the due date and the grace period string

    So far it parses out three different pieces of time information:
        self.display_due_date - the 'official' due date that gets displayed to students
        self.grace_period - the length of the grace period
        self.close_date - the real due date

    """
    _delta_standin = Timedelta()

    def __init__(self, due_date, grace_period_string_or_timedelta):
        if due_date is not None:
            self.display_due_date = due_date

        else:
            self.display_due_date = None

        if grace_period_string_or_timedelta is not None and self.display_due_date:
            if isinstance(grace_period_string_or_timedelta, six.string_types):
                try:
                    self.grace_period = TimeInfo._delta_standin.from_json(grace_period_string_or_timedelta)
                except:
                    log.error("Error parsing the grace period {0}".format(grace_period_string_or_timedelta))
                    raise
            else:
                self.grace_period = grace_period_string_or_timedelta
            self.close_date = self.display_due_date + self.grace_period
        else:
            self.grace_period = None
            self.close_date = self.display_due_date
