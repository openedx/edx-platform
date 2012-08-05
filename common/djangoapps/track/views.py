import json
import logging
import os
import datetime
import dateutil.parser

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http import Http404
from django.shortcuts import redirect
from django.conf import settings
from mitxmako.shortcuts import render_to_response

from django_future.csrf import ensure_csrf_cookie
from track.models import TrackingLog

log = logging.getLogger("tracking")

LOGFIELDS = ['username','ip','event_source','event_type','event','agent','page','time']

def log_event(event):
    event_str = json.dumps(event)
    log.info(event_str[:settings.TRACK_MAX_EVENT])
    if settings.MITX_FEATURES.get('ENABLE_SQL_TRACKING_LOGS'):
        event['time'] = dateutil.parser.parse(event['time'])
        tldat = TrackingLog(**dict([(x,event[x]) for x in LOGFIELDS]))
        try:
            tldat.save()
        except Exception as err:
            log.debug(err)

def user_track(request):
    try:  # TODO: Do the same for many of the optional META parameters
        username = request.user.username
    except:
        username = "anonymous"

    try:
        scookie = request.META['HTTP_COOKIE']  # Get cookies
        scookie = ";".join([c.split('=')[1] for c in scookie.split(";") if "sessionid" in c]).strip()  # Extract session ID
    except:
        scookie = ""

    try:
        agent = request.META['HTTP_USER_AGENT']
    except:
        agent = ''

    # TODO: Move a bunch of this into log_event
    event = {
        "username": username,
        "session": scookie,
        "ip": request.META['REMOTE_ADDR'],
        "event_source": "browser",
        "event_type": request.GET['event_type'],
        "event": request.GET['event'],
        "agent": agent,
        "page": request.GET['page'],
        "time": datetime.datetime.utcnow().isoformat(),
        }
    log_event(event)
    return HttpResponse('success')


def server_track(request, event_type, event, page=None):
    try:
        username = request.user.username
    except:
        username = "anonymous"

    try:
        agent = request.META['HTTP_USER_AGENT']
    except:
        agent = ''

    event = {
        "username": username,
        "ip": request.META['REMOTE_ADDR'],
        "event_source": "server",
        "event_type": event_type,
        "event": event,
        "agent": agent,
        "page": page,
        "time": datetime.datetime.utcnow().isoformat(),
        }

    if event_type=="/event_logs" and request.user.is_staff:	# don't log
        return
    log_event(event)

@login_required
@ensure_csrf_cookie
def view_tracking_log(request):
    if not request.user.is_staff:
        return redirect('/')
    record_instances = TrackingLog.objects.all().order_by('-time')[0:100]
    return render_to_response('tracking_log.html',{'records':record_instances})

