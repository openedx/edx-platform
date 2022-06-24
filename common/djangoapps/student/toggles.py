"""
Toggles for Dashboard page.
"""
from edx_toggles.toggles import WaffleFlag


# Namespace for student waffle flags.
WAFFLE_FLAG_NAMESPACE = 'student'

# Waffle flag to enable amplitude recommendations
# .. toggle_name: student.enable_amplitude_recommendations
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports rollout of a POC for amplitude recommendations.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-06-24
# .. toggle_target_removal_date: None
# .. toggle_warning: None
# .. toggle_tickets: VAN-984
ENABLE_AMPLITUDE_RECOMMENDATIONS = WaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.enable_amplitude_recommendations', __name__)


def should_show_amplitude_recommendations():
    return ENABLE_AMPLITUDE_RECOMMENDATIONS.is_enabled()
