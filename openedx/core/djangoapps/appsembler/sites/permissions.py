from rest_framework import permissions


class AMCAdminPermission(permissions.BasePermission):
    """
    Allow making changes only if you're designated as an admin in AMC.
    """

    def has_permission(self, request, view):
        is_microsite_admin = request.user.usersitemapping_set.filter(is_amc_admin=True).exists()
        is_organization_admin = request.user.userorganizationmapping_set.filter(is_amc_admin=True).exists()
        is_superuser = request.user.is_superuser
        return is_microsite_admin or is_organization_admin or is_superuser
