"""
This module contains the data models for the import_from_modulestore app.
"""
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ImportStatus(TextChoices):
    """
    The status of this course import.
    """

    # PENDING: The import has been created, but the OLX and related data are not yet in the library.
    # It is not ready to be read.
    PENDING = 'pending', _('Pending')
    # READY: The content is staged and ready to be read.
    READY = 'ready', _('Ready')
    # IMPORTED: The content has been imported into the library.
    IMPORTED = 'imported', _('Imported')
    # CANCELED: The import was canceled before it was imported.
    CANCELED = 'canceled', _('Canceled')
    # ERROR: The content could not be imported.
    ERROR = 'error', _('Error')
