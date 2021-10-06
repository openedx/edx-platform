"""
Various helpful utilities for ESG
"""
import json

from opaque_keys.edx.keys import UsageKey
from rest_framework.request import clone_request

from lms.djangoapps.courseware.module_render import handle_xblock_callback


def call_xblock_json_handler(request, usage_id, handler_name, data):
    """
    Create an internally-routed XBlock.json_handler request.
    The internal auth code/param unpacking requires a POST request with payload in the body.

    params:
        request (HttpRequest): Originating web request, we're going to borrow auth headers/cookies from this
        usage_id (str): Usage ID of the XBlock for running the handler
        handler_name (str): the name of the XBlock handler method
        data (dict): Data to be encoded and sent as the body of the POST request
    """
    # XBlock.json_handler operates through a POST request
    proxy_request = clone_request(request, "POST")
    proxy_request.META["REQUEST_METHOD"] = "POST"

    # The body is an encoded JSON blob
    proxy_request.body = json.dumps(data).encode()

    # Course ID can be retrieved from the usage_id
    usage_key = UsageKey.from_string(usage_id)
    course_id = str(usage_key.course_key)

    # Send and decode the request
    response = handle_xblock_callback(proxy_request, course_id, usage_id, handler_name)
    return json.loads(response.content)
