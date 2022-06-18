"""
App for creating and distributing CSRF tokens to frontend applications.
"""

from django.apps import AppConfig


class CsrfAppConfig(AppConfig):
    """Configuration for the csrf application."""

    name = 'csrf'
    verbose_name = 'CSRF'
