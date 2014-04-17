""" Permissions classes utilized by Django REST Framework """
import logging

from django.conf import settings

from rest_framework import permissions

log = logging.getLogger(__name__)


class ApiKeyHeaderPermission(permissions.BasePermission):
    """
    Check for permissions by matching the configured API key and header

    """
    def has_permission(self, request, view):
        """
        If settings.DEBUG is True and settings.EDX_API_KEY is not set or None,
        then allow the request. Otherwise, allow the request if and only if
        settings.EDX_API_KEY is set and the X-Edx-Api-Key HTTP header is
        present in the request and matches the setting.
        """

        debug_enabled = settings.DEBUG
        api_key = getattr(settings, "EDX_API_KEY", None)

        # DEBUG mode rules over all else
        # Including the api_key check here ensures we don't break the feature locally
        if debug_enabled and api_key is None:
            log.warn("EDX_API_KEY Override: Debug Mode")
            return True

        # If we're not DEBUG, we need a local api key
        if api_key is None:
            return False

        # The client needs to present the same api key
        header_key = request.META.get('HTTP_X_EDX_API_KEY')
        if header_key is None:
            try:
                header_key = request.META['headers'].get('X-Edx-Api-Key')
            except KeyError:
                return False
            if header_key is None:
                return False

        # The api key values need to be the same
        if header_key != api_key:
            return False

        # Allow the request to take place
        return True
