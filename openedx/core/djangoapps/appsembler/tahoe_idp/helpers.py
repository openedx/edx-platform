"""
Helper module for Tahoe Identity Provider package.

 - https://github.com/appsembler/tahoe-idp/
"""

from collections import OrderedDict

from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode

from site_config_client.openedx import api as config_client_api

import third_party_auth
from third_party_auth.pipeline import running as pipeline_running


from .constants import TAHOE_IDP_BACKEND_NAME


def is_tahoe_idp_enabled():
    """
    Tahoe: Check if tahoe-idp package is enabled for the current site (or cluster-wide).
    """
    global_flag = settings.FEATURES.get('ENABLE_TAHOE_IDP', False)
    return config_client_api.get_admin_value('ENABLE_TAHOE_IDP', default=global_flag)


def get_idp_login_url(next_url=None):
    """
    Get Tahoe IdP login URL which uses `social_auth`.
    """
    params = OrderedDict()
    params['auth_entry'] = 'login'
    if next_url:
        params['next'] = next_url

    base = reverse('social:begin', args=[TAHOE_IDP_BACKEND_NAME])
    return '{base}?{query}'.format(
        base=base,
        query=urlencode(params),
    )


def get_idp_register_url(next_url=None):
    """
    Get Tahoe IdP register URL using `tahoe-idp` package.
    """
    base = '/register-use-fa-form'

    if not next_url:
        return base

    params = {
        'next': next_url,
    }

    return '{base}?{query}'.format(
        base=base,
        query=urlencode(params),
    )


def get_idp_form_url(request, initial_form_mode, next_url):
    """
    Get the login/register URLs for the identity provider.

    Disable upstream login/register forms when the Tahoe Identity Provider is enabled.
    """
    if not is_tahoe_idp_enabled():
        return None

    if not third_party_auth.is_enabled():
        return None

    if initial_form_mode == "register":
        if pipeline_running(request):
            # Upon registration, Open edX  auto-submits the frontend hidden registration form.
            # Returning, None to avoid breaking an otherwise needed form submit.
            return None

        return get_idp_register_url(next_url=next_url)
    else:
        return get_idp_login_url(next_url=next_url)
