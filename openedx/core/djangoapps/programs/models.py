"""Models providing Programs support for the LMS and Studio."""
from config_models.models import ConfigurationModel
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProgramsApiConfig(ConfigurationModel):
    """
    This model no longer fronts an API, but now sets a few config-related values for the idea of programs in general.

    A rename to ProgramsConfig would be more accurate, but costly in terms of developer time.

    .. no_pii:
    """
    class Meta:
        app_label = "programs"

    marketing_path = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            'Path used to construct URLs to programs marketing pages (e.g., "/foo").'
        )
    )
