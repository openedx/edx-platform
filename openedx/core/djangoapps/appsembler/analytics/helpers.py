"""
Helpers for the Appsembler Analytics app.
"""

from organizations.models import UserOrganizationMapping


def should_show_hubspot(user):
    if not user or not user.is_authenticated:
        return False

    if not user.is_active:
        return False

    if user.is_superuser or user.is_staff:
        return False

    mapping = UserOrganizationMapping.objects.get(user=user)
    if not (mapping.is_amc_admin and mapping.is_active):
        return False

    return True
