"""
Module for code that should run during LMS and CMS startup.
"""

from django.conf import settings

# pylint: disable=invalid-name


def run():
    """
    Executed during django startup
    """
    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False):
        enable_third_party_auth_for_sudo()


def enable_third_party_auth_for_sudo():
    """
    Enable the use of third_party_auth for django-sudo, which allows users to re-authenticate
    using other identity providers to get sudo access.
    """

    from django_sudo_helpers import settings as sudo_auth_settings
    sudo_auth_settings.apply_settings(settings)
