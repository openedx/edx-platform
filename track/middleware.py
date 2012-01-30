import json

from django.conf import settings

import views

class TrackMiddleware:
    def process_request(self, request):
        try:
            # We're already logging events, and we don't want to capture user
            # names/passwords.
            if request.META['PATH_INFO'] in ['/event', '/login']:
                return
            
            event = { 'GET'  : dict(request.GET),
                      'POST' : dict(request.POST)}
            
            # TODO: Confirm no large file uploads
            event = json.dumps(event)
            event = event[:512]

            views.server_track(request, request.META['PATH_INFO'], event)
        except:
            pass
