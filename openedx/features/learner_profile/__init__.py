"""
Learner profile settings and helper methods.
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlag, WaffleFlagNamespace


# Namespace for learner profile waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='learner_profile')

# Waffle flag to redirect to another learner profile experience.
# .. toggle_name: REDIRECT_TO_PROFILE_MICROFRONTEND
# .. toggle_type: waffle_flag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout of a new micro-frontend-based implementation of the profile page.
# .. toggle_category: micro-frontend
# .. toggle_use_cases: incremental_release, open_edx
# .. toggle_creation_date: 2019-02-19
# .. toggle_expiration_date: 2020-12-31
# .. toggle_warnings: Remember to also set PROFILE_MICROFRONTEND_URL before this toggle is enabled.
# .. toggle_tickets: DEPR-17
# .. toggle_status: supported
REDIRECT_TO_PROFILE_MICROFRONTEND = WaffleFlag(WAFFLE_FLAG_NAMESPACE, 'redirect_to_microfrontend')
