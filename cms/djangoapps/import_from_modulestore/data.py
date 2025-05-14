"""
This module contains the data models for the import_from_modulestore app.
"""
from collections import namedtuple
from enum import Enum
from openedx.core.djangoapps.content_libraries import api as content_libraries_api

from django.utils.translation import gettext_lazy as _


class ImportStatus(Enum):
    """
    The status of this modulestore-to-learning-core import.
    """

    WAITNG_TO_STAGE = _('Waiting to stage content')
    STAGING = _('Staging content for import')
    STAGING_FAILED = _('Failed to stage content')
    STAGED = _('Content is staged and ready for import')
    IMPORTING = _('Importing staged content')
    IMPORTING_FAILED = _('Failed to import staged content')
    IMPORTED = _('Staged content imported successfully')
    CANCELED = _('Import canceled')

    FAILED_STATUSES = [
        STAGING_FAILED,
        IMPORTING_FAILED,
    ]


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

    @classmethod
    def choices(cls):
        """
        Returns all levels of composition levels as a list of tuples.
        """
        return [
            (composition_level.value, composition_level.name)
            for composition_level in cls
            if not isinstance(composition_level.value, list)
        ]


PublishableVersionWithMapping = namedtuple('PublishableVersionWithMapping', ['publishable_version', 'mapping'])
