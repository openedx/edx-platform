"""
Helper module for Tahoe Auth0.

 - https://github.com/appsembler/tahoe-auth0/
"""
from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def is_tahoe_auth0_enabled():
    """
    Tahoe: Check if tahoe-auth0 package is enabled for the current site (or cluster-wide).
    """
    is_enabled = configuration_helpers.get_value(
        'ENABLE_TAHOE_AUTH0',
        settings.FEATURES.get('ENABLE_TAHOE_AUTH0', False),
    )
    return is_enabled
