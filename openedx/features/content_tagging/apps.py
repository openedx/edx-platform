"""
Define the content tagging Django App.
"""

from django.apps import AppConfig


class ContentTaggingConfig(AppConfig):
    """App config for the content tagging feature"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "openedx.features.content_tagging"
