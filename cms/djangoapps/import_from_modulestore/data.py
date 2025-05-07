"""
This module contains the data models for the import_from_modulestore app.
"""
from collections import namedtuple
from enum import Enum
from openedx.core.djangoapps.content_libraries import api as content_libraries_api

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


class CompositionLevel(Enum):
    """
    Enumeration of composition levels for course content.
    Defines the different levels of composition for course content,
    including chapters, sequentials, verticals, and xblocks.
    It also categorizes these levels into complicated and flat
    levels for easier processing.
    """

    CHAPTER = content_libraries_api.ContainerType.Section
    SEQUENTIAL = content_libraries_api.ContainerType.Subsection
    VERTICAL = content_libraries_api.ContainerType.Unit
    COMPONENT = 'component'
    OLX_COMPLEX_LEVELS = [
        VERTICAL.olx_tag,
        SEQUENTIAL.olx_tag,
        CHAPTER.olx_tag,
    ]

    @classmethod
    def values(cls):
        """
        Returns all levels of composition levels.
        """
        return [composition_level.value for composition_level in cls]


PublishableVersionWithMapping = namedtuple('PublishableVersionWithMapping', ['publishable_version', 'mapping'])
