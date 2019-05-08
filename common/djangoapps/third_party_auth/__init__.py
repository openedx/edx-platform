"""Third party authentication. """

from __future__ import absolute_import
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.waffle_utils import WaffleSwitchNamespace, WaffleSwitch

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

default_app_config = 'third_party_auth.apps.ThirdPartyAuthConfig'

# Namespace for Third party authentication app waffle switches
THIRD_PARTY_AUTH_WAFFLE_SWITCHES = WaffleSwitchNamespace(name='third_party_auth')

# Waffle flag to enable Okta IdP started authentication
ENABLE_OKTA_AUTH_FIX = WaffleSwitch(THIRD_PARTY_AUTH_WAFFLE_SWITCHES, 'enable_okta_auth_fix')


def is_enabled():
    """Check whether third party authentication has been enabled. """

    # We do this import internally to avoid initializing settings prematurely
    from django.conf import settings

    return configuration_helpers.get_value(
        "ENABLE_THIRD_PARTY_AUTH",
        settings.FEATURES.get("ENABLE_THIRD_PARTY_AUTH")
    )
