import beeline


class HoneycombLegacyMiddleware(object):
    """ legacy honeycomb middleware

    The default middleware for Honeycomb ('beeline.middleware.django.HoneyMiddleware')
    does not work with MIDDLEWARE_CLASSES, instead requring the newer (as of Django 1.10)
    MIDDLEWARE. Until we are on a version of Open edX that has switched to MIDDLEWARE,
    we have to use a different middleware.

    This implements the bare minimum of honeycomb request instrumentation in a
    MIDDLEWARE_CLASSES compatible version.

    It just creates a trace with the basic request/response data. The fields
    match the beeline version as much as possible so we should be able to use
    standard queries.

    Features that this is missing:

       * database query tracing (even beeline only gets that with a Django 2.0+ API)
       * adding error data on failed requests
       * distributed tracing (normally a HTTP_X_HONEYCOMB_TRACE HTTP header
         would be detected and this service's trace would be attached
         to the trace of the calling service)
    """

    def process_request(self, request):
        request_context = self.get_context_from_request(request)
        request.honeycomb_trace = beeline.start_trace(context=request_context)

        return None

    def process_response(self, request, response):
        # at this point we know the response status code
        beeline.add_context_field("response.status_code", response.status_code)
        # send it on its way
        if hasattr(request, 'honeycomb_trace'):
            # if another piece of middleware runs earlier and generates a
            # redirect or error response, `process_request()` will be skipped
            # on subsequent middlewares (like ours). Hence, we have to
            # check that our trace is there before trying to send it.
            # For full instrumentation, you should make sure that this
            # middleware is earlier in MIDDLEWARE_CLASSES than others
            # that might do that, such as Django's CommonMiddleware
            beeline.finish_trace(request.honeycomb_trace)

        return response

    def get_context_from_request(self, request):
        trace_name = "django_http_%s" % request.method.lower()
        return {
            "name": trace_name,
            "type": "http_server",
            "request.host": request.get_host(),
            "request.method": request.method,
            "request.path": request.path,
            "request.remote_addr": request.META.get('REMOTE_ADDR'),
            "request.content_length": request.META.get('CONTENT_LENGTH', 0),
            "request.user_agent": request.META.get('HTTP_USER_AGENT'),
            "request.scheme": request.scheme,
            "request.secure": request.is_secure(),
            "request.query": request.GET.dict(),
            "request.xhr": request.is_ajax(),
        }
