"""
Utility methods related to proctoring configurations.
"""


from django.conf import settings


def get_proctoring_config(config_name, default, proctoring_provider="DEFAULT"):
    """
    Returns the value of config_name from the default proctoring backend if set or default.
    """
    proctoring_backend = settings.PROCTORING_BACKENDS.get(proctoring_provider, None)
    return proctoring_backend.get(config_name, default) if proctoring_backend else default


def requires_escalation_email(proctoring_provider="DEFAULT"):
    """
    Returns the value of 'requires_escalation_email' in the given proctoring backend.
    The default value for 'requires_escalation_email' is False.
    """
    return get_proctoring_config("requires_escalation_email", False, proctoring_provider)


def show_review_rules(proctoring_provider="DEFAULT"):
    """
    Returns the value of 'show_review_rules' in the given proctoring backend.
    The default value for 'show_review_rules' True.
    """
    return get_proctoring_config("show_review_rules", True, proctoring_provider)
