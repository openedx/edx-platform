"""
Django-based logging utilities

UserIdFilter: A logging.Filter that adds userid to the logging context
"""
from __future__ import absolute_import

from logging import Filter

from crum import get_current_user


class UserIdFilter(Filter):
    def filter(self, record):
        user = get_current_user()
        if user and user.pk:
            record.userid = user.pk
        else:
            record.userid = None
        return True
