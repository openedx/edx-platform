"""
This module contains the data models for the import_from_modulestore app.
"""
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ImportStatus(TextChoices):
    """
    The status of this modulestore-to-learning-core import.
    """

    NOT_STARTED = 'not_started', _('Waiting to stage content')
    STAGING = 'staging', _('Staging content for import')
    STAGING_FAILED = _('Failed to stage content')
    STAGED = 'staged', _('Content is staged and ready for import')
    IMPORTING = 'importing', _('Importing staged content')
    IMPORTING_FAILED = 'importing_failed', _('Failed to import staged content')
    IMPORTED = 'imported', _('Successfully imported content')
    CANCELED = 'canceled', _('Canceled')
