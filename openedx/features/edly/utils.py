import logging

import jwt
import waffle
from django.conf import settings
from django.forms.models import model_to_dict

from openedx.features.edly.models import EdlySubOrganization
from util.organizations_helpers import get_organizations

LOGGER = logging.getLogger(__name__)

def encode_edly_user_info_cookie(cookie_data):
    """
    Encode edly_user_info cookie data into JWT string.

    Arguments:
        cookie_data (dict): Edly user info cookie dict.

    Returns:
        string
    """
    return jwt.encode(cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithm=settings.EDLY_JWT_ALGORITHM)

def decode_edly_user_info_cookie(encoded_cookie_data):
    """
    Decode edly_user_info cookie data from JWT string.

    Arguments:
        encoded_cookie_data (dict): Edly user info cookie JWT encoded string.

    Returns:
        dict
    """
    return jwt.decode(encoded_cookie_data, settings.EDLY_COOKIE_SECRET_KEY, algorithms=[settings.EDLY_JWT_ALGORITHM])

def get_enabled_organizations(request):
    """
    Helper method to get linked organizations for request site.

    Returns:
        list: List of linked organizations for request site
    """

    if not waffle.switch_is_active(settings.ENABLE_EDLY_ORGANIZATIONS_SWITCH):
        return get_organizations()

    try:
        studio_site_edx_organization = model_to_dict(request.site.studio_site.edx_organization)
    except EdlySubOrganization.DoesNotExist:
        LOGGER.exception('No EdlySubOrganization found for site %s', request.site)
        return []

    return [studio_site_edx_organization]
