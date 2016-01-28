"""
This middleware is used for cleaning headers from a response before it is sent to the end user.

Due to the nature of how middleware runs, a piece of middleware high in the chain cannot ensure
that response headers won't be present on the final response body, as middleware further down
the chain could be adding them.

This middleware is intended to sit as close as possible to the top of the list, so that it has
a chance on the reponse going out to strip the intended headers.
"""


def remove_headers_from_response(response, *headers):
    """Removes the given headers from the response using the clean_headers middleware."""
    response.clean_headers = headers
