"""
Signal handlers for Content Library Collections.
"""

import logging

from django.dispatch import receiver
from openedx_events.content_authoring.data import LibraryCollectionData
from openedx_events.content_authoring.signals import (
    LIBRARY_COLLECTION_CREATED,
    LIBRARY_COLLECTION_UPDATED,
    LIBRARY_COLLECTION_DELETED,
)


log = logging.getLogger(__name__)


@receiver(LIBRARY_COLLECTION_CREATED)
def library_collection_created_handler(**kwargs):
    """
    Content Library Collection Created signal handler
    """
    library_collection_data = kwargs.get("library_collection", None)
    if not library_collection_data or not isinstance(library_collection_data, LibraryCollectionData):
        log.error("Received null or incorrect data for event")
        return

    log.info("Received Collection Created Signal")

    # TODO: Implement handler logic


@receiver(LIBRARY_COLLECTION_UPDATED)
def library_collection_updated_handler(**kwargs):
    """
    Content Library Collection Updated signal handler
    """
    library_collection_data = kwargs.get("library_collection", None)
    if not library_collection_data or not isinstance(library_collection_data, LibraryCollectionData):
        log.error("Received null or incorrect data for event")
        return

    log.info("Received Collection Updated Signal")


@receiver(LIBRARY_COLLECTION_DELETED)
def library_collection_deleted_handler(**kwargs):
    """
    Content Library Collection Deleted signal handler
    """
    library_collection_data = kwargs.get("library_collection", None)
    if not library_collection_data or not isinstance(library_collection_data, LibraryCollectionData):
        log.error("Received null or incorrect data for event")
        return

    log.info("Received Collection Deleted Signal")
