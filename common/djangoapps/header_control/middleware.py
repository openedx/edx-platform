"""
Middleware used for adjusting headers in a response before it is sent to the end user.
"""


class HeaderControlMiddleware(object):
    """
    Middleware that can modify/remove headers in a response.

    This can be used, for example, to remove headers i.e. drop any Vary headers to improve cache performance.
    """

    def process_response(self, _request, response):
        """
        Processes the given response, potentially remove or modifying headers.
        """

        if len(getattr(response, 'remove_headers', [])) > 0:
            for header in response.remove_headers:
                try:
                    del response[header]
                except KeyError:
                    pass

        if len(getattr(response, 'force_headers', {})) > 0:
            for header, value in response.force_headers.iteritems():
                try:
                    del response[header]
                except KeyError:
                    pass

                response[header] = value

        return response
