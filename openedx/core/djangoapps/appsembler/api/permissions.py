"""Provides permissions for Tahoe API

Code adapted from Figures

"""
import django.contrib.sites.shortcuts

from rest_framework.permissions import BasePermission
from rest_framework.throttling import UserRateThrottle

from organizations.models import (
    Organization,
    UserOrganizationMapping,
)


def is_site_admin_user(request):

    current_site = django.contrib.sites.shortcuts.get_current_site(request)

    # get orgs for the site
    orgs = Organization.objects.filter(sites__in=[current_site])

    # Should just be mappings for organizations in this site
    # If just one organization in a site, then the queryset returned
    # should contain just one element

    uom_qs = UserOrganizationMapping.objects.filter(
        organization__in=orgs,
        user=request.user)

    # Since Tahoe does just one org, we're going to cheat and just look
    # for the first element
    if uom_qs:
        return uom_qs[0].is_amc_admin and uom_qs[0].is_active
    else:
        return False


class IsSiteAdminUser(BasePermission):
    """

    We need to stick with a Site Admin unless we have a way to identify the org
    from the URL/host/virtual host
    """
    def has_permission(self, request, view):
        return is_site_admin_user(request)


class TahoeAPIUserThrottle(UserRateThrottle):
    """
    Limit the rate of requests users can make to the Tahoe API
    """
    rate = '60/minute'
