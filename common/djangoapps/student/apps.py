"""
Configuration for the ``student`` Django application.
"""
from __future__ import absolute_import

from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class StudentConfig(AppConfig):
    """
    Default configuration for the ``student`` application.
    """
    name = 'student'

    def ready(self):
        from django.contrib.auth.models import update_last_login as django_update_last_login
        user_logged_in.disconnect(django_update_last_login)
        from .signals.receivers import update_last_login
        user_logged_in.connect(update_last_login)
