class XForwardedForMiddleware(object):
    """
    Middleware for rewriting REMOTE_ADDR when behind a proxy
    """

    def process_request(self, request):
        """
        Rewrite the REMOTE_ADDR header using HTTP_X_FORWARDED_FOR
        """
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_FORWARDED_FOR']
        return None
