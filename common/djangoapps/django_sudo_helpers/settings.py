"""
Settings for the django-sudo module.
"""


def apply_settings(django_settings):
    """Set provider-independent settings."""
    django_settings.SOCIAL_AUTH_PIPELINE += ('django_sudo_helpers.pipeline.create_sudo_session',)
