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


# Waffle flag to enable fallback recommendations.
# .. toggle_name: student.enable_fallback_recommendations
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports showing fallback recommendation in case of error on amplitude side.
#                        Currently, fallback recommendations are picked from settings.GENERAL_RECOMMENDATIONS.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2023-01-16
# .. toggle_target_removal_date: None
# .. toggle_warning: None
# .. toggle_tickets: VAN-1239
ENABLE_FALLBACK_RECOMMENDATIONS = WaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.enable_fallback_recommendations', __name__)


def show_fallback_recommendations():
    return ENABLE_FALLBACK_RECOMMENDATIONS.is_enabled()


# Waffle flag to enable 2U Recommendations
# .. toggle_name: student.enable_2u_recommendations
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports rollout of a POC for 2U recommendations.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2022-09-20
# .. toggle_target_removal_date: None
# .. toggle_warning: None
# .. toggle_tickets: VAN-1094
ENABLE_2U_RECOMMENDATIONS_ON_DASHBOARD = WaffleFlag(f'{WAFFLE_FLAG_NAMESPACE}.enable_2u_recommendations', __name__)


def should_show_2u_recommendations():
    return ENABLE_2U_RECOMMENDATIONS_ON_DASHBOARD.is_enabled()


# Waffle flag to enable course enrollment confirmation email.
# .. toggle_name: student.enable_enrollment_confirmation_email
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enable course enrollment email template
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2022-08-05
# .. toggle_target_removal_date: None
# .. toggle_warning: None
# .. toggle_tickets: VAN-1129
ENROLLMENT_CONFIRMATION_EMAIL = WaffleFlag(
    f'{WAFFLE_FLAG_NAMESPACE}.enable_enrollment_confirmation_email', __name__
)


def should_send_enrollment_email():
    return ENROLLMENT_CONFIRMATION_EMAIL.is_enabled()
