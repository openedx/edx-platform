"""
Middleware used for cleaning headers from a response before it is sent to the end user.
"""


class CleanHeadersMiddleware(object):
    """
    Middleware that can drop headers present in a response.

    This can be used, for example, to remove headers i.e. drop any Vary headers to improve cache performance.
    """

    def process_response(self, _request, response):
        """
        Processes the given response, potentially stripping out any unwanted headers.
        """

        if len(getattr(response, 'clean_headers', [])) > 0:
            for header in response.clean_headers:
                try:
                    del response[header]
                except KeyError:
                    pass

        return response
