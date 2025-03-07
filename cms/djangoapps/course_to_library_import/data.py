"""
This module contains the data models for the course_to_library_import app.
"""

from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class CourseToLibraryImportStatus(TextChoices):
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
    # ERROR: The content could not be imported.
    ERROR = 'error', _('Error')
