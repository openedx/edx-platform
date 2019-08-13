"""
Heplers for site/org isolations functions.
"""
from openedx.core.djangoapps.theming.helpers import get_current_site

from organizations.models import Organization, UserOrganizationMapping


def user_exists_in_organization(user_email, organization):
    """
    TODO
    """
    return organization.userorganizationmapping_set.filter(user__email=user_email).exists()


def get_organization_for_site(site):
    """
    TODO
    """
    return get_current_site().organizations.first()


def get_user_in_organization_by_email(user_email, organization):
    """
    TODO
    """
    try:
        user = organization.userorganizationmapping_set.get(user__email=user_email).user
        return user
    except UserOrganizationMapping.DoesNotExist:
        return None
