import datetime
import json

import pytz

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect

from django.views.decorators.csrf import ensure_csrf_cookie

from edxmako.shortcuts import render_to_response

from track import tracker
from track import contexts
from track import shim
from track.models import TrackingLog
from eventtracking import tracker as eventtracker


def log_event(event):
    """Capture a event by sending it to the register trackers"""
    tracker.send(event)


def _get_request_header(request, header_name, default=''):
    """Helper method to get header values from a request's META dict, if present."""
    if request is not None and hasattr(request, 'META') and header_name in request.META:
        return request.META[header_name]
    else:
        return default


def _get_request_value(request, value_name, default=''):
    """Helper method to get header values from a request's REQUEST dict, if present."""
    if request is not None and hasattr(request, 'REQUEST') and value_name in request.REQUEST:
        return request.REQUEST[value_name]
    else:
        return default


def user_track(request):
    """
    Log when POST call to "event" URL is made by a user. Uses request.REQUEST
    to allow for GET calls.

    GET or POST call should provide "event_type", "event", and "page" arguments.
    """
    try:
        username = request.user.username
    except:
        username = "anonymous"

    name = _get_request_value(request, 'event_type')
    data = _get_request_value(request, 'event', {})
    page = _get_request_value(request, 'page')

    if isinstance(data, basestring) and len(data) > 0:
        try:
            data = json.loads(data)
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
        "ip": _get_request_header(request, 'REMOTE_ADDR'),
        "referer": _get_request_header(request, 'HTTP_REFERER'),
        "accept_language": _get_request_header(request, 'HTTP_ACCEPT_LANGUAGE'),
        "event_source": "server",
        "event_type": event_type,
        "event": event,
        "agent": _get_request_header(request, 'HTTP_USER_AGENT'),
        "page": page,
        "time": datetime.datetime.utcnow(),
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

    # All fields must be specified, in case the tracking information is
    # also saved to the TrackingLog model.  Get values from the task-level
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
            "time": datetime.datetime.utcnow(),
            "host": request_info.get('host', 'unknown'),
            "context": eventtracker.get_tracker().resolve_context(),
        }

    log_event(event)


@login_required
@ensure_csrf_cookie
def view_tracking_log(request, args=''):
    """View to output contents of TrackingLog model.  For staff use only."""
    if not request.user.is_staff:
        return redirect('/')
    nlen = 100
    username = ''
    if args:
        for arg in args.split('/'):
            if arg.isdigit():
                nlen = int(arg)
            if arg.startswith('username='):
                username = arg[9:]

    record_instances = TrackingLog.objects.all().order_by('-time')
    if username:
        record_instances = record_instances.filter(username=username)
    record_instances = record_instances[0:nlen]

    # fix dtstamp
    fmt = '%a %d-%b-%y %H:%M:%S'  # "%Y-%m-%d %H:%M:%S %Z%z"
    for rinst in record_instances:
        rinst.dtstr = rinst.time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern')).strftime(fmt)

    return render_to_response('tracking_log.html', {'records': record_instances})
