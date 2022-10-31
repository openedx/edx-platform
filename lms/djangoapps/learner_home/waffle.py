"""
This module contains various configuration settings via
waffle switches for the teams app.
"""

from edx_toggles.toggles import WaffleFlag
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# Namespace for Learner Home MFE waffle flags.
WAFFLE_FLAG_NAMESPACE = "learner_home_mfe"

# .. toggle_name: learner_home_mfe.enabled
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable to redirect user to learner home mfe
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2022-10-11
# .. toggle_tickets: AU-879
ENABLE_LEARNER_HOME_MFE = WaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.enabled",
    __name__,
)


def should_redirect_to_learner_home_mfe():
    return configuration_helpers.get_value(
        "ENABLE_LEARNER_HOME_MFE", ENABLE_LEARNER_HOME_MFE.is_enabled()
    )


# Waffle flag to enable to recommendation panel on learner home mfe
# .. toggle_name: learner_home_mfe.enable_learner_home_amplitude_recommendations
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable to recommendation panel on learner home mfe
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-10-28
# .. toggle_target_removal_date: None
# .. toggle_warning: None
# .. toggle_tickets: VAN-1138
ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS = WaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.enable_learner_home_amplitude_recommendations", __name__
)


def should_show_learner_home_amplitude_recommendations():
    return ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS.is_enabled()
