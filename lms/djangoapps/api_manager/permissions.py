""" Permissions classes utilized by Django REST Framework """
import logging

from django.conf import settings

from api_manager.utils import get_client_ip_address, address_exists_in_network
from rest_framework import permissions
from rest_framework.views import APIView


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


class IPAddressRestrictedPermission(permissions.BasePermission):
    """
    Check for permissions by matching the request IP address
    against the allowed ip address(s)
    """

    def has_permission(self, request, view):
        ip_address = get_client_ip_address(request)
        allowed_ip_addresses = getattr(settings, 'ALLOWED_IP_ADDRESSES', None)
        if allowed_ip_addresses:
            for allowed_ip_address in allowed_ip_addresses:
                if '/' in allowed_ip_address:
                    is_allowed = address_exists_in_network(ip_address, allowed_ip_address)
                    if is_allowed:
                        return is_allowed
                else:
                    if ip_address == allowed_ip_address:
                        return True
            log.warn("{} is not allowed to access Api".format(ip_address))
            return False
        else:
            return True


class SecureAPIView(APIView):
    """
        Inherited from APIView
    """
    permission_classes = (ApiKeyHeaderPermission, IPAddressRestrictedPermission)
