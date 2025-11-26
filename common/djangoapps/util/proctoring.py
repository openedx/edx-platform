"""
Utility methods related to proctoring configurations.
"""


from django.conf import settings


def requires_escalation_email(proctoring_provider):
    """
    Returns the value of 'requires_escalation_email' in the given proctoring backend.
    The default value for 'requires_escalation_email' is False.
    """
    return settings.PROCTORING_BACKENDS.get(proctoring_provider, {}).get(
        "requires_escalation_email", False
    )


def show_review_rules(proctoring_provider):
    """
    Returns the value of 'show_review_rules' in the given proctoring backend.
    The default value for 'show_review_rules' is True.
    """
    return settings.PROCTORING_BACKENDS.get(proctoring_provider, {}).get(
        "show_review_rules", True
    )
