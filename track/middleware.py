import views, json

class TrackMiddleware:
    def process_request (self, request):
        try:
            # We're already logging events
            if request.META['PATH_INFO'] == '/event':
                return
            
            event = { 'GET'  : dict(request.GET),
                      'POST' : dict(request.POST)}
            
            # TODO: Confirm no large file uploads
            event = json.dumps(event)
            event = event[:512]

            views.server_track(request, request.META['PATH_INFO'], event)
        except:
            pass
