"""
Toggles for Learner Profile page.
"""


from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# Namespace for learner profile waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='learner_profile')

# Waffle flag to redirect to another learner profile experience.
# .. toggle_name: learner_profile.redirect_to_microfrontend
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of a new micro-frontend-based implementation of the profile page.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2019-02-19
# .. toggle_target_removal_date: 2020-12-31
# .. toggle_warnings: Also set settings.PROFILE_MICROFRONTEND_URL and site's ENABLE_PROFILE_MICROFRONTEND.
# .. toggle_tickets: DEPR-17
REDIRECT_TO_PROFILE_MICROFRONTEND = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'redirect_to_microfrontend', __name__)


def should_redirect_to_profile_microfrontend():
    return (
        configuration_helpers.get_value('ENABLE_PROFILE_MICROFRONTEND') and
        REDIRECT_TO_PROFILE_MICROFRONTEND.is_enabled()
    )
