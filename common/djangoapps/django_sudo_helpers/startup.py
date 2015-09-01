"""
Module for code that should run during LMS and CMS startup.
"""

from django.conf import settings

# pylint: disable=invalid-name


def run():
    """
    Executed during django startup
    """
    if settings.FEATURES.get('ENABLE_DJANGO_SUDO', False):
        enable_django_sudo()


def enable_django_sudo():
    """
    Enable the use of django-sudo, which allows users to re-authenticate
    using their password or other identity providers to get sudo access.
    """

    from django_sudo_helpers import settings as sudo_auth_settings
    sudo_auth_settings.apply_settings(settings)
