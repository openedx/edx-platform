"""
Toggles for user_authn
"""


from django.conf import settings

from edx_toggles.toggles import WaffleFlag
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_request

# .. toggle_name: ENABLE_REQUIRE_THIRD_PARTY_AUTH
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: Set to True to prevent using username/password login and registration and only allow authentication with third party auth
# .. toggle_category: admin
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2020-09-16
# .. toggle_expiration_date: None
# .. toggle_tickets: None
# .. toggle_status: supported
# .. toggle_warnings: Requires configuration of third party auth


def is_require_third_party_auth_enabled():
    # TODO: Replace function with SettingToggle when it is available.
    return getattr(settings, "ENABLE_REQUIRE_THIRD_PARTY_AUTH", False)

# .. toggle_name: user_authn.redirect_to_microfrontend
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of a new micro-frontend-based implementation of the login and registration pages
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2021-02-02
# .. toggle_target_removal_date: None
# .. toggle_warnings: Also set settings.AUTHN_MICROFRONTEND_URL and site's ENABLE_AUTHN_MICROFRONTEND
# .. toggle_tickets: VAN-308
REDIRECT_TO_AUTHN_MICROFRONTEND = WaffleFlag('user_authn.redirect_to_microfrontend', __name__)


def should_redirect_to_authn_microfrontend():
    """
    Checks if login/registration should be done via MFE.
    """
    request = get_current_request()
    if request and request.GET.get('skip_authn_mfe'):
        return False

    return configuration_helpers.get_value(
        'ENABLE_AUTHN_MICROFRONTEND', settings.FEATURES.get('ENABLE_AUTHN_MICROFRONTEND')
    ) and REDIRECT_TO_AUTHN_MICROFRONTEND.is_enabled()
