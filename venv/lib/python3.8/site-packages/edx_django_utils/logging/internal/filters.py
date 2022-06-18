"""
Django-based logging filters
"""

from logging import Filter

from crum import get_current_request, get_current_user


class RemoteIpFilter(Filter):
    """
    A logging filter that adds the remote IP to the logging context
    """
    def filter(self, record):
        request = get_current_request()
        if request and 'REMOTE_ADDR' in request.META:
            record.remoteip = request.META['REMOTE_ADDR']
        else:
            record.remoteip = None
        return True


class UserIdFilter(Filter):
    """
    A logging filter that adds userid to the logging context
    """
    def filter(self, record):
        user = get_current_user()
        if user and user.pk:
            record.userid = user.pk
        else:
            record.userid = None
        return True
