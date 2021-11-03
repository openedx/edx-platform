"""
Various helpful utilities for ESG
"""
from functools import wraps
import json

from django.http.response import HttpResponseBadRequest

from opaque_keys.edx.keys import UsageKey
from rest_framework.request import clone_request

from lms.djangoapps.courseware.module_render import handle_xblock_callback


def require_params(param_names):
    """
    Adds the required query params to the view function. Returns 404 if param(s) missing.

    Params:
    - param_name (string): the query param to unpack

    Raises:
    - 404 if the param was not provided
    """
    def decorator(function):
        @wraps(function)
        def wrapped_function(self, request, *args, **kwargs):  # pylint: disable=unused-argument
            passed_parameters = []

            for param_name in param_names:
                param = request.query_params.get(param_name)

                if not param:
                    return HttpResponseBadRequest(f"Query requires the following query params: {', '.join(param_names)}")

                passed_parameters.append(param)
            return function(self, request, *passed_parameters, *args, **kwargs)
        return wrapped_function
    return decorator


def call_xblock_json_handler(request, usage_id, handler_name, data, decode=True):
    """
    Create an internally-routed XBlock.json_handler request.
    The internal auth code/param unpacking requires a POST request with payload in the body.

    params:
        request (HttpRequest): Originating web request, we're going to borrow auth headers/cookies from this
        usage_id (str): Usage ID of the XBlock for running the handler
        handler_name (str): the name of the XBlock handler method
        data (dict): Data to be encoded and sent as the body of the POST request
        decode (Boolean): Whether to return just the decoded body (True, default) or the original HttpReponse (False)
    returns:
        content (Dict) or response (HttpResponse): depending on whether decode is True (Dict) or False (HttpResponse)
    """
    # XBlock.json_handler operates through a POST request
    proxy_request = clone_request(request, "POST")
    proxy_request.META["REQUEST_METHOD"] = "POST"

    # The body is an encoded JSON blob
    proxy_request.body = json.dumps(data).encode()

    # Course ID can be retrieved from the usage_id
    usage_key = UsageKey.from_string(usage_id)
    course_id = str(usage_key.course_key)

    # Send the request
    response = handle_xblock_callback(proxy_request, course_id, usage_id, handler_name)

    # And decode if requested
    if decode:
        return json.loads(response.content)
    else:
        return response
