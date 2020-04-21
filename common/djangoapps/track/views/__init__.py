

import datetime
import json

import pytz
import six
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from eventtracking import tracker as eventtracker
from ipware.ip import get_ip

from edxmako.shortcuts import render_to_response
from track import contexts, shim, tracker


def log_event(event):
    """Capture a event by sending it to the register trackers"""
    tracker.send(event)


def _get_request_header(request, header_name, default=''):
    """Helper method to get header values from a request's META dict, if present."""
    if request is not None and hasattr(request, 'META') and header_name in request.META:
        return request.META[header_name]
    else:
        return default


def _get_request_ip(request, default=''):
    """Helper method to get IP from a request's META dict, if present."""
    if request is not None and hasattr(request, 'META'):
        return get_ip(request)
    else:
        return default


def _get_request_value(request, value_name, default=''):
    """Helper method to get header values from a request's GET/POST dict, if present."""
    if request is not None:
        if request.method == 'GET':
            return request.GET.get(value_name, default)
        elif request.method == 'POST':
            return request.POST.get(value_name, default)
    return default


def _add_user_id_for_username(data):
    """
    If data contains a username, adds the corresponding user_id to the data.

    In certain use cases, the caller may have the username and not the
    user_id. This enables us to standardize on user_id in event data,
    even when the caller only has access to the username.
    """
    if data and ('username' in data) and ('user_id' not in data):
        try:
            user = User.objects.get(username=data.get('username'))
            data['user_id'] = user.id
        except User.DoesNotExist:
            pass


def user_track(request):
    """
    Log when POST call to "event" URL is made by a user.

    GET or POST call should provide "event_type", "event", and "page" arguments.
    """
    try:
        username = request.user.username
    except:
        username = "anonymous"

    name = _get_request_value(request, 'event_type')
    data = _get_request_value(request, 'event', {})
    page = _get_request_value(request, 'page')

    if isinstance(data, six.string_types) and len(data) > 0:
        try:
            data = json.loads(data)
            _add_user_id_for_username(data)
        except ValueError:
            pass

    context_override = contexts.course_context_from_url(page)
    context_override['username'] = username
    context_override['event_source'] = 'browser'
    context_override['page'] = page

    with eventtracker.get_tracker().context('edx.course.browser', context_override):
        eventtracker.emit(name=name, data=data)

    return HttpResponse('success')


def server_track(request, event_type, event, page=None):
    """
    Log events related to server requests.

    Handle the situation where the request may be NULL, as may happen with management commands.
    """
    if event_type.startswith("/event_logs") and request.user.is_staff:
        return  # don't log

    try:
        username = request.user.username
    except:
        username = "anonymous"

    # define output:
    event = {
        "username": username,
        "ip": _get_request_ip(request),
        "referer": _get_request_header(request, 'HTTP_REFERER'),
        "accept_language": _get_request_header(request, 'HTTP_ACCEPT_LANGUAGE'),
        "event_source": "server",
        "event_type": event_type,
        "event": event,
        "agent": _get_request_header(request, 'HTTP_USER_AGENT').encode().decode('latin1'),
        "page": page,
        "time": datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
        "host": _get_request_header(request, 'SERVER_NAME'),
        "context": eventtracker.get_tracker().resolve_context(),
    }

    # Some duplicated fields are passed into event-tracking via the context by track.middleware.
    # Remove them from the event here since they are captured elsewhere.
    shim.remove_shim_context(event)

    log_event(event)


def task_track(request_info, task_info, event_type, event, page=None):
    """
    Logs tracking information for events occuring within celery tasks.

    The `event_type` is a string naming the particular event being logged,
    while `event` is a dict containing whatever additional contextual information
    is desired.

    The `request_info` is a dict containing information about the original
    task request.  Relevant keys are `username`, `ip`, `agent`, and `host`.
    While the dict is required, the values in it are not, so that {} can be
    passed in.

    In addition, a `task_info` dict provides more information about the current
    task, to be stored with the `event` dict.  This may also be an empty dict.

    The `page` parameter is optional, and allows the name of the page to
    be provided.
    """

    # supplement event information with additional information
    # about the task in which it is running.
    full_event = dict(event, **task_info)

    # Get values from the task-level
    # information, or just add placeholder values.
    with eventtracker.get_tracker().context('edx.course.task', contexts.course_context_from_url(page)):
        event = {
            "username": request_info.get('username', 'unknown'),
            "ip": request_info.get('ip', 'unknown'),
            "event_source": "task",
            "event_type": event_type,
            "event": full_event,
            "agent": request_info.get('agent', 'unknown'),
            "page": page,
            "time": datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
            "host": request_info.get('host', 'unknown'),
            "context": eventtracker.get_tracker().resolve_context(),
        }

    log_event(event)
