"""
Toggles for verify_student app
"""

from openedx.core.djangoapps.waffle_utils import WaffleFlagNamespace, WaffleFlag

# Namespace for verify_students waffle flags.
WAFFLE_FLAG_NAMESPACE = WaffleFlagNamespace(name='verify_student')

# Waffle flag to use new email templates for sending ID verification emails.
# .. toggle_name: verify_student.use_new_email_templates
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Supports staged rollout to students for a new email templates implementation for ID verification.
# .. toggle_category: verify student
# .. toggle_use_cases: incremental_release, open_edx
# .. toggle_creation_date: 2020-06-25
# .. toggle_expiration_date: n/a
# .. toggle_warnings: n/a
# .. toggle_tickets: PROD-1639
# .. toggle_status: supported
USE_NEW_EMAIL_TEMPLATES = WaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='use_new_email_templates',
    flag_undefined_default=False
)


def use_new_templates_for_id_verification_emails():
    return USE_NEW_EMAIL_TEMPLATES.is_enabled()
