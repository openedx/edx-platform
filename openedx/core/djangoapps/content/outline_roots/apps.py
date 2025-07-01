"""
Outline Roots Django application initialization.
"""

from django.apps import AppConfig


class OutlineRootsConfig(AppConfig):
    """
    Configuration for the OutlineRoot Django application.
    """

    name = "openedx.core.djangoapps.content.outline_roots"
    verbose_name = "Learning Core Course Prototype > Outline Roots"
    default_auto_field = "django.db.models.BigAutoField"
    label = "oel_outline_roots"

    def ready(self):
        """
        Register Section and SectionVersion.
        """
        from openedx_learning.api.authoring import register_content_models  # pylint: disable=import-outside-toplevel
        from .models import OutlineRoot, OutlineRootVersion  # pylint: disable=import-outside-toplevel

        register_content_models(OutlineRoot, OutlineRootVersion)
