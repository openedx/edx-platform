"""
Third party auth API related permissions
"""
from rest_framework import permissions

from third_party_auth.models import ProviderApiPermissions


class ThirdPartyAuthProviderApiPermission(permissions.BasePermission):
    """
    Allow someone to access the view if they have valid OAuth client credential.
    """
    def __init__(self, provider_id):
        """ Initialize the class with a provider_id """
        self.provider_id = provider_id

    def has_permission(self, request, view):
        """
        Check if the OAuth client associated with auth token in current request has permission to access
        the information for provider
        """
        if not request.auth or not self.provider_id:
            # doesn't have access token or no provider_id specified
            return False

        try:
            ProviderApiPermissions.objects.get(client__pk=request.auth.client_id, provider_id=self.provider_id)
        except ProviderApiPermissions.DoesNotExist:
            return False

        return True
