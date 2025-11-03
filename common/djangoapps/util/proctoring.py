"""
Utility methods related to proctoring configurations.
"""


from django.conf import settings


def get_default_proctoring_config(config_name, default):
    """
    Returns the value of config_name from the default proctoring backend if set or default.
    """
    default_backend = settings.PROCTORING_BACKENDS.get("DEFAULT", None)
    backend_config = (
        settings.PROCTORING_BACKENDS.get(default_backend, {})
        if default_backend
        else {}
    )
    return backend_config.get(config_name, default)


def requires_escalation_email():
    """
    Returns the value of 'requires_escalation_email' in the default proctoring backend.
    The default value is False.
    """
    return get_default_proctoring_config("requires_escalation_email", False)


def show_review_rules():
    """
    Returns the value of 'show_review_rules' in the default default proctoring backend.
    The default value is True.
    """
    return get_default_proctoring_config("show_review_rules", True)
