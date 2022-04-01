"""
Helper module for Tahoe Identity Provider package.

 - https://github.com/appsembler/tahoe-idp/
"""

from django.conf import settings

from site_config_client.openedx import api as config_client_api

TAHOE_IDP_BACKEND_NAME = 'tahoe-idp'


def is_tahoe_idp_enabled():
    """
    Tahoe: Check if tahoe-idp package is enabled for the current site (or cluster-wide).
    """
    global_flag = settings.FEATURES.get('ENABLE_TAHOE_IDP', False)
    # TODO: Remove `ENABLE_TAHOE_IDP` once we update Product Signup
    legacy = config_client_api.get_admin_value('ENABLE_TAHOE_IDP', default=global_flag)
    new = config_client_api.get_admin_value('ENABLE_TAHOE_IDP', default=global_flag)
    return legacy or new
