from logging import getLogger

from openedx.features.edly.models import (
    EdlySubOrganization,
    EdlyUserProfile
)

logger = getLogger(__name__)


def is_edly_user_allowed_to_login(request, possibly_authenticated_user):
    """
    Check if the user is allowed to login on the current site.

    This method checks if the user has edly sub organization of current
    site in it's edly sub organizations list.

    Arguments:
        request (object): HTTP request object
        possibly_authenticated_user (User): User object trying to authenticate

    Returns:
        bool: Returns True if User has Edly Sub Organization Access Otherwise False.
    """

    if possibly_authenticated_user.is_superuser:
        return True

    try:
        edly_sub_org = request.site.edly_sub_org_for_lms
    except EdlySubOrganization.DoesNotExist:
        logger.error('Edly sub organization does not exist for site %s.' % request.site)
        return False

    try:
        edly_user_profile = possibly_authenticated_user.edly_profile
    except EdlyUserProfile.DoesNotExist:
        logger.warning('User %s has no edly profile for site %s.' % (possibly_authenticated_user.email, request.site))
        return False

    if edly_sub_org.slug in edly_user_profile.get_linked_edly_sub_organizations:
        return True

    return False
