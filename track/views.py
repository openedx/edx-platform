# Create your views here.
from django.http import HttpResponse
from django.http import Http404
from django.conf import settings
import json, os, stat

import tempfile

if settings.TRACK_DIR != None:
    directory = tempfile.mkdtemp(prefix = settings.TRACK_DIR)
else:
    directory = None

logfile = None
file_index = 0 
log_index = 0
filename = None

def make_file():
    global logfile, log_index, file_index, filename
    if logfile != None:
        logfile.close()
        os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR | \
                           stat.S_IRGRP | stat.S_IWGRP | \
                           stat.S_IROTH )
    filename = directory+"/%05i"%(file_index)+".trklog"
    logfile = open(filename, "w")
    file_index = file_index + 1
    log_index = 0

def log_event(event):
    global logfile, log_index
    event_str = json.dumps(event)
    if settings.TRACK_DIR == None:
#        print event
        return

    if logfile == None or log_index >= settings.MAXLOG:
        make_file()

    logfile.write(event_str[:settings.TRACK_MAX_EVENT]+'\n')
    if settings.DEBUG_TRACK_LOG:
        print event_str
    log_index = log_index + 1

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
