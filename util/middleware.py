import logging

from django.http import HttpResponse

log = logging.getLogger("mitx")

class ExceptionLoggingMiddleware(object):
    """Just here to log unchecked exceptions that go all the way up the Django 
    stack"""

    def process_exception(self, request, exception):
        log.exception(exception)
        return HttpResponse("Server Error - Please try again later.")
