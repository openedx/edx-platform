"""
Heplers for site/org isolations functions.
"""
from openedx.core.djangoapps.theming.helpers import get_current_site

from organizations.models import Organization, UserOrganizationMapping


def user_exists_in_organization(user_email, organization):
    """
    Look is a user exists inside an organization based on a given email

    `user_email` is the user email
    `organization` the organization object

    returns True or False
        Representing is the user exists or not inside the org
    """
    return organization.userorganizationmapping_set.filter(user__email=user_email).exists()


def get_organization_for_site(site):
    """
    Returns an organization based in a given site.

    `site` is the Site object

    returns an organization or None
    """
    return get_current_site().organizations.first()


def get_user_in_organization_by_email(user_email, organization):
    """
    Return a user inside an organization based on a given email

    `user_email` is the user email
    `organization` the organization object

    returns the User object or UserOrganizationMapping.DoesNotExist
    """
    try:
        user = organization.userorganizationmapping_set.get(user__email=user_email).user
        return user
    except UserOrganizationMapping.DoesNotExist:
        return None
