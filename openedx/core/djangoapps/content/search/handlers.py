"""
Signal/event handlers for content search
"""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver
from openedx_events.content_authoring.data import ContentLibraryData, ContentObjectData, LibraryBlockData, XBlockData
from openedx_events.content_authoring.signals import (
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    XBLOCK_CREATED,
    XBLOCK_DELETED,
    XBLOCK_UPDATED,
    CONTENT_OBJECT_TAGS_CHANGED,
)
from openedx.core.djangoapps.content_tagging.utils import get_content_key_from_string

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.search.models import SearchAccess

from .api import only_if_meilisearch_enabled, upsert_block_tags_index_docs
from .tasks import (
    delete_library_block_index_doc,
    delete_xblock_index_doc,
    update_content_library_index_docs,
    upsert_library_block_index_doc,
    upsert_xblock_index_doc
)

log = logging.getLogger(__name__)


# Using post_delete here because there is no COURSE_DELETED event defined.
@receiver(post_delete, sender=CourseOverview)
def delete_course_search_access(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """Deletes the SearchAccess instance for deleted CourseOverview"""
    SearchAccess.objects.filter(context_key=instance.id).delete()


@receiver(CONTENT_LIBRARY_DELETED)
def delete_library_search_access(content_library: ContentLibraryData, **kwargs):
    """Deletes the SearchAccess instance for deleted content libraries"""
    SearchAccess.objects.filter(context_key=content_library.library_key).delete()


@receiver(XBLOCK_CREATED)
@only_if_meilisearch_enabled
def xblock_created_handler(**kwargs) -> None:
    """
    Create the index for the XBlock
    """
    xblock_info = kwargs.get("xblock_info", None)
    if not xblock_info or not isinstance(xblock_info, XBlockData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    upsert_xblock_index_doc.delay(
        str(xblock_info.usage_key),
        recursive=False,
    )


@receiver(XBLOCK_UPDATED)
@only_if_meilisearch_enabled
def xblock_updated_handler(**kwargs) -> None:
    """
    Update the index for the XBlock and its children
    """
    xblock_info = kwargs.get("xblock_info", None)
    if not xblock_info or not isinstance(xblock_info, XBlockData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    upsert_xblock_index_doc.delay(
        str(xblock_info.usage_key),
        recursive=True,  # Update all children because the breadcrumb may have changed
    )


@receiver(XBLOCK_DELETED)
@only_if_meilisearch_enabled
def xblock_deleted_handler(**kwargs) -> None:
    """
    Delete the index for the XBlock
    """
    xblock_info = kwargs.get("xblock_info", None)
    if not xblock_info or not isinstance(xblock_info, XBlockData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    delete_xblock_index_doc.delay(str(xblock_info.usage_key))


@receiver(LIBRARY_BLOCK_CREATED)
@only_if_meilisearch_enabled
def library_block_updated_handler(**kwargs) -> None:
    """
    Create or update the index for the content library block
    """
    library_block_data = kwargs.get("library_block", None)
    if not library_block_data or not isinstance(library_block_data, LibraryBlockData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    upsert_library_block_index_doc.delay(str(library_block_data.usage_key))


@receiver(LIBRARY_BLOCK_DELETED)
@only_if_meilisearch_enabled
def library_block_deleted(**kwargs) -> None:
    """
    Delete the index for the content library block
    """
    library_block_data = kwargs.get("library_block", None)
    if not library_block_data or not isinstance(library_block_data, LibraryBlockData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    delete_library_block_index_doc.delay(str(library_block_data.usage_key))


@receiver(CONTENT_LIBRARY_UPDATED)
@only_if_meilisearch_enabled
def content_library_updated_handler(**kwargs) -> None:
    """
    Update the index for the content library
    """
    content_library_data = kwargs.get("content_library", None)
    if not content_library_data or not isinstance(content_library_data, ContentLibraryData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    update_content_library_index_docs.delay(str(content_library_data.library_key))


@receiver(CONTENT_OBJECT_TAGS_CHANGED)
@only_if_meilisearch_enabled
def content_object_tags_changed_handler(**kwargs) -> None:
    """
    Update the tags data in the index for the Content Object
    """
    content_object_tags = kwargs.get("content_object", None)
    if not content_object_tags or not isinstance(content_object_tags, ContentObjectData):
        log.error("Received null or incorrect data for event")
        return

    try:
        # Check if valid if course or library block
        get_content_key_from_string(content_object_tags.object_id)
    except ValueError:
        log.error("Received invalid content object id")
        return

    upsert_block_tags_index_docs(content_object_tags.object_id)
