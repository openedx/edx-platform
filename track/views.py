import json
import logging
import os

# Create your views here.
from django.http import HttpResponse
from django.http import Http404
from django.conf import settings

log = logging.getLogger("tracking")

def log_event(event):
    event_str = json.dumps(event)
    log.info(event_str[:settings.TRACK_MAX_EVENT])

def user_track(request):
    try: # TODO: Do the same for many of the optional META parameters
        username = request.user.username
    except: 
        username = "anonymous"

    # TODO: Move a bunch of this into log_event
    event = {
        "username" : username,
        "session" : request.META['HTTP_COOKIE'],
        "ip" : request.META['REMOTE_ADDR'],
        "event_source" : "browser",
        "event_type" : request.GET['event_type'], 
        "event" : request.GET['event'],
        "agent" : request.META['HTTP_USER_AGENT'],
        "page" : request.GET['page'],
        }
    log_event(event)
    return HttpResponse('success')

def server_track(request, event_type, event, page=None):
    try: 
        username = request.user.username
    except: 
        username = "anonymous"

    event = {
        "username" : username, 
        "ip" : request.META['REMOTE_ADDR'],
        "event_source" : "server",
        "event_type" : event_type, 
        "event" : event,
        "agent" : request.META['HTTP_USER_AGENT'],
        "page" : page,
        }
    log_event(event)
