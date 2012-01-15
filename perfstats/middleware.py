import views, json, tempfile
import hotshot
import hotshot.stats
from django.conf import settings

tmpfile = None
prof = None
isRunning = False

def restart_profile():
    global prof, tmpfile, isRunning
    try: 
        oldname = tmpfile.name
    except: 
        oldname = ""
    if prof != None:
        if isRunning:
            prof.stop() 
        prof.close()
    tmpfile = tempfile.NamedTemporaryFile(prefix='prof',delete=False)
    prof = hotshot.Profile(tmpfile.name, lineevents=1)
    isRunning = False
    print "Filename", tmpfile.name
    return (tmpfile.name, oldname)

restart_profile()

class ProfileMiddleware:
    def process_request (self, request):
        global isRunning
        if not isRunning:
            prof.start()
            isRunning = True
        else:
            print "Profiler was already running. Results may be unpredictable"
        
        print "Process request"

    def process_response (self, request, response):
        global isRunning
        if isRunning:
            prof.stop()
            isRunning = False
        print "Process response"
        return response
