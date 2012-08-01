import logging

from django.conf import settings
from django.http import HttpResponseServerError

log = logging.getLogger("mitx")


class ExceptionLoggingMiddleware(object):
    """Just here to log unchecked exceptions that go all the way up the Django
    stack"""

    if not settings.TEMPLATE_DEBUG:
        def process_exception(self, request, exception):
            log.exception(exception)
            return HttpResponseServerError("Server Error - Please try again later.")
