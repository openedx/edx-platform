""" Helper functions for the contentstore API views. """
from rest_framework import serializers
from django.http import HttpResponseBadRequest


def _validate(request, context=None):
    """
    Validates the request data using the context's associated serializer.
    
    Args:
    - request: the incoming request object.
    - context: the current view object with a `serializer_class` attribute.
    
    Raises:
    - serializers.ValidationError: if the request data is invalid.
    """
    serializer = context.get_serializer(data=request.data)
    serializer.is_valid(raise_exception=True)


def run_if_valid(request, context=None, callback=None):
    """
    Validates the request body using the provided context's serializer.
    If valid, it runs the callback; otherwise, returns a 400 response.

    Assumes the view using this has a `serializer_class` attribute.

    Args:
    - request: the incoming request object.
    - context: the current view object. Typically used as `context=self`.
    - callback: the function to execute if the request is valid.

    Usage:
    ```
    def create(self, request):
        callback = lambda: upload_transcript(request)
        return run_if_valid(request, context=self, callback=callback)
    ```
    """
    try:
        _validate(request, context)
        return callback()
    except serializers.ValidationError as e:
        return HttpResponseBadRequest(reason=e.detail)
