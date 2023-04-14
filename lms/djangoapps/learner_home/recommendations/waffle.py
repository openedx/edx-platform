"""
Configuration of recommendation feature for Learner Home.
"""

from edx_toggles.toggles import WaffleFlag

# Namespace for Learner Home MFE waffle flags.
WAFFLE_FLAG_NAMESPACE = "learner_home_mfe"

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
