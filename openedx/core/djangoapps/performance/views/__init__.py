"""
Views for logging performance data.
"""
import datetime
import json
import logging

from django.http import HttpResponse

from track.utils import DateTimeJSONEncoder


log = logging.getLogger("perflog")


def _get_request_header(request, header_name, default=''):
    """Helper method to get header values from a request's META dict, if present."""
    if request is not None and hasattr(request, 'META') and header_name in request.META:
        return request.META[header_name]
    else:
        return default


def _get_request_value(request, value_name, default=''):
    """Helper method to get header values from a request's GET or POST dicts, if present."""
    if request is not None and hasattr(request, 'GET') and value_name in request.GET:
        return request.GET[value_name]
    elif request is not None and hasattr(request, 'POST') and value_name in request.POST:
        return request.POST[value_name]
    else:
        return default


def performance_log(request):
    """
    Log when POST call to "performance" URL is made by a user.
    Request should provide "event" and "page" arguments.
    """

    event = {
        "ip": _get_request_header(request, 'REMOTE_ADDR'),
        "referer": _get_request_header(request, 'HTTP_REFERER'),
        "accept_language": _get_request_header(request, 'HTTP_ACCEPT_LANGUAGE'),
        "event_source": "browser",
        "event": _get_request_value(request, 'event'),
        "agent": _get_request_header(request, 'HTTP_USER_AGENT'),
        "page": _get_request_value(request, 'page'),
        "id": _get_request_value(request, 'id'),
        "expgroup": _get_request_value(request, 'expgroup'),
        "value": _get_request_value(request, 'value'),
        "time": datetime.datetime.utcnow(),
        "host": _get_request_header(request, 'SERVER_NAME'),
    }

    log.info(json.dumps(event, cls=DateTimeJSONEncoder))

    return HttpResponse(status=204)
