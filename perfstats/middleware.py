import views, json, tempfile
import hotshot
import hotshot.stats
from django.conf import settings

tmpfile = None
prof = None

def restart_profile():
    global prof, tmpfile
    try: 
        oldname = tmpfile.name
    except: 
        oldname = ""
    if prof != None:
        prof.close()
    tmpfile = tempfile.NamedTemporaryFile(prefix='prof',delete=False)
    prof = hotshot.Profile(tmpfile.name)
    print "Filename", tmpfile.name
    return (tmpfile.name, oldname)

restart_profile()

class ProfileMiddleware:
    def process_request (self, request):
        prof.start()
        print "Process request"

    def process_response (self, request, response):
        try: 
            prof.stop()
        except:
            print "Profiler not active. If you didn't just restart, this is an error"
        print "Process response"
        return response
