from rest_framework import permissions

from tahoe_sites.models import UserOrganizationMapping


class AMCAdminPermission(permissions.BasePermission):
    """
    Allow making changes only if you're designated as an admin in AMC.
    """

    # TODO: RED-2845 Remove this class when AMC is removed.
    def has_permission(self, request, view):
        is_organization_admin = UserOrganizationMapping.objects.filter(
            user=request.user,
            is_admin=True,
        ).exists()
        is_superuser = request.user.is_superuser
        return request.user.is_active and (is_organization_admin or is_superuser)
