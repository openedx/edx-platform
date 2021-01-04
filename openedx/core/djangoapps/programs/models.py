"""Models providing Programs support for the LMS and Studio."""


import six
from config_models.models import ConfigurationModel
from django.db import models
from django.utils.translation import ugettext_lazy as _


class ProgramsApiConfig(ConfigurationModel):
    """
    This model no longer fronts an API, but now sets a few config-related values for the idea of programs in general.

    A rename to ProgramsConfig would be more accurate, but costly in terms of developer time.

    .. no_pii:
    """
    class Meta(object):
        app_label = "programs"

    marketing_path = models.CharField(
        max_length=255,
        blank=True,
        help_text=_(
            'Path used to construct URLs to programs marketing pages (e.g., "/foo").'
        )
    )


class CustomProgramsConfig(ConfigurationModel):  # pylint: disable=model-missing-unicode, useless-suppression
    """
    Manages configuration for a run of the backpopulate_program_credentials management command.
    """
    class Meta(object):
        app_label = 'programs'
        verbose_name = 'backpopulate_program_credentials argument'

    arguments = models.TextField(
        blank=True,
        help_text='Useful for manually running a Jenkins job. Specify like "--usernames A B --program-uuids X Y".',
        default='',
    )

    def __str__(self):
        return six.text_type(self.arguments)
