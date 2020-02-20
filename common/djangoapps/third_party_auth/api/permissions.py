"""
Third party auth API related permissions
"""

import logging

from edx_django_utils.monitoring import set_custom_metric
from edx_rest_framework_extensions.auth.jwt.decoder import decode_jwt_filters
from edx_rest_framework_extensions.permissions import (
    IsSuperuser,
    JwtHasScope,
    JwtRestrictedApplication,
    NotJwtRestrictedApplication
)
from rest_condition import C
from rest_framework.permissions import BasePermission
from third_party_auth.models import ProviderApiPermissions

from openedx.core.lib.api.permissions import ApiKeyHeaderPermission

log = logging.getLogger(__name__)


class ThirdPartyAuthProviderApiPermission(BasePermission):
    """
    Allow someone to access the view if they have valid OAuth client credential.

    Deprecated: Only works for DOP oauth applications. To be removed as part of DOPrecation.

    """
    def has_permission(self, request, view):
        """
        Check if the OAuth client associated with auth token in current request has permission to access
        the information for provider
        """
        provider_id = view.kwargs.get('provider_id')
        if not request.auth or not provider_id:
            # doesn't have access token or no provider_id specified
            return False

        try:
            ProviderApiPermissions.objects.get(client__pk=request.auth.client_id, provider_id=provider_id)
        except ProviderApiPermissions.DoesNotExist:
            return False

        set_custom_metric('deprecated_ThirdPartyAuthProviderApiPermission', True)
        return True


class JwtHasTpaProviderFilterForRequestedProvider(BasePermission):
    """
    Ensures the JWT used to authenticate contains the appropriate tpa_provider
    filter for the provider_id requested in the view.
    """
    message = 'JWT missing required tpa_provider filter.'

    def has_permission(self, request, view):
        """
        Ensure that the provider_id kwarg provided to the view exists exists
        in the tpa_provider filters in the JWT used to authenticate.
        """
        provider_id = view.kwargs.get('provider_id')
        if not provider_id:
            log.warning("Permission JwtHasTpaProviderFilterForRequestedProvider requires a view with provider_id.")
            return False

        jwt_filters = decode_jwt_filters(request.auth)
        for filter_type, filter_value in jwt_filters:
            if filter_type == 'tpa_provider' and filter_value == provider_id:
                return True

        log.warning(
            "Permission JwtHasTpaProviderFilterForRequestedProvider: required filter tpa_provider:%s was not found.",
            provider_id,
        )
        return False


# TODO: Remove ApiKeyHeaderPermission. Check deprecated_api_key_header custom metric for active usage.
_NOT_JWT_RESTRICTED_TPA_PERMISSIONS = (
    C(NotJwtRestrictedApplication) &
    (C(IsSuperuser) | ApiKeyHeaderPermission | ThirdPartyAuthProviderApiPermission)
)
_JWT_RESTRICTED_TPA_PERMISSIONS = (
    C(JwtRestrictedApplication) &
    JwtHasScope &
    JwtHasTpaProviderFilterForRequestedProvider
)
TPA_PERMISSIONS = (
    (_NOT_JWT_RESTRICTED_TPA_PERMISSIONS | _JWT_RESTRICTED_TPA_PERMISSIONS)
)
