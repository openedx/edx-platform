"""
This middleware is used for adjusting the headers in a response before it is sent to the end user.

This middleware is intended to sit as close as possible to the top of the middleare list as possible,
so that it is one of the last pieces of middleware to touch the response, and thus can most accurately
adjust/control the headers of the response.
"""


def remove_headers_from_response(response, *headers):
    """Removes the given headers from the response using the header_control middleware."""
    response.remove_headers = headers


def force_header_for_response(response, header, value):
    """Forces the given header for the given response using the header_control middleware."""
    force_headers = {}
    if hasattr(response, 'force_headers'):
        force_headers = response.force_headers
    force_headers[header] = value

    response.force_headers = force_headers
