"""
Toggles for verify_student app
"""

from edx_toggles.toggles import WaffleFlag, WaffleFlagNamespace

# Namespace for verify_students waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='verify_student')

# Waffle flag to use new email templates for sending ID verification emails.
# .. toggle_name: verify_student.use_new_email_templates
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout to students for a new email templates
#   implementation for ID verification.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-06-25
# .. toggle_target_removal_date: None
# .. toggle_warnings: This temporary feature toggle does not have a target removal date.
# .. toggle_tickets: PROD-1639
USE_NEW_EMAIL_TEMPLATES = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='use_new_email_templates',
    module_name=__name__,
)


def use_new_templates_for_id_verification_emails():
    return USE_NEW_EMAIL_TEMPLATES.is_enabled()


# Waffle flag to redirect to the new IDV flow on the account microfrontend
# .. toggle_name: verify_student.redirect_to_idv_microfrontend
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout to students for the new IDV flow.
# .. toggle_use_cases: temporary, open_edx
# .. toggle_creation_date: 2020-07-09
# .. toggle_target_removal_date: None
# .. toggle_warnings: This temporary feature toggle does not have a target removal date.
# .. toggle_tickets: MST-318
REDIRECT_TO_IDV_MICROFRONTEND = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='redirect_to_idv_microfrontend',
    module_name=__name__,
)


def redirect_to_idv_microfrontend():
    return REDIRECT_TO_IDV_MICROFRONTEND.is_enabled()
