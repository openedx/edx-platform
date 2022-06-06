"""Provides permissions for Tahoe API

Code adapted from Figures

"""
import logging

import django.contrib.sites.shortcuts

from rest_framework.permissions import BasePermission
from rest_framework.throttling import UserRateThrottle

from organizations.models import Organization
from tahoe_sites.api import get_organization_by_site, is_active_admin_on_organization

log = logging.getLogger(__name__)


def is_site_admin_user(request):

    current_site = django.contrib.sites.shortcuts.get_current_site(request)

    # get orgs for the site
    try:
        organization = get_organization_by_site(site=current_site)
    except Organization.DoesNotExist:
        return False
    except Organization.MultipleObjectsReturned:
        log.warning(
            'is_site_admin_user: This module expects a one:one relationship between organization and site. '
            'Raised by site (%s)', current_site.id
        )
        return False

    return is_active_admin_on_organization(user=request.user, organization=organization)


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
