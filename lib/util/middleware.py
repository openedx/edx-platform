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

# From http://djangosnippets.org/snippets/1042/
def parse_accept_header(accept):
    """Parse the Accept header *accept*, returning a list with pairs of
    (media_type, q_value), ordered by q values.
    """
    result = []
    for media_range in accept.split(","):
        parts = media_range.split(";")
        media_type = parts.pop(0)
        media_params = []
        q = 1.0
        for part in parts:
            (key, value) = part.lstrip().split("=", 1)
            if key == "q":
                q = float(value)
            else:
                media_params.append((key, value))
        result.append((media_type, tuple(media_params), q))
    result.sort(lambda x, y: -cmp(x[2], y[2]))
    return result

class AcceptMiddleware(object):
    def process_request(self, request):
        accept = parse_accept_header(request.META.get("HTTP_ACCEPT", ""))
        request.accept = accept
        request.accepted_types = map(lambda (t, p, q): t, accept)
