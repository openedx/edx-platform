"""
Signal/event handlers for content search
"""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryCollectionLocator
from openedx_events.content_authoring.data import (
    ContentLibraryData,
    ContentObjectChangedData,
    LibraryBlockData,
    LibraryCollectionData,
    XBlockData,
)
from openedx_events.content_authoring.signals import (
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    LIBRARY_BLOCK_UPDATED,
    LIBRARY_COLLECTION_CREATED,
    LIBRARY_COLLECTION_DELETED,
    LIBRARY_COLLECTION_UPDATED,
    XBLOCK_CREATED,
    XBLOCK_DELETED,
    XBLOCK_UPDATED,
    CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
)

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.search.models import SearchAccess

from .api import (
    only_if_meilisearch_enabled,
    upsert_block_collections_index_docs,
    upsert_block_tags_index_docs,
    upsert_collection_tags_index_docs,
)
from .tasks import (
    delete_library_block_index_doc,
    delete_xblock_index_doc,
    update_content_library_index_docs,
    update_library_collection_index_doc,
    upsert_library_block_index_doc,
    upsert_xblock_index_doc,
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
@receiver(LIBRARY_BLOCK_UPDATED)
@only_if_meilisearch_enabled
def library_block_updated_handler(**kwargs) -> None:
    """
    Create or update the index for the content library block
    """
    library_block_data = kwargs.get("library_block", None)
    if not library_block_data or not isinstance(library_block_data, LibraryBlockData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    # Update content library index synchronously to make sure that search index is updated before
    # the frontend invalidates/refetches results. This is only a single document update so is very fast.
    upsert_library_block_index_doc.apply(args=[str(library_block_data.usage_key)])


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

    # Update content library index synchronously to make sure that search index is updated before
    # the frontend invalidates/refetches results. This is only a single document update so is very fast.
    delete_library_block_index_doc.apply(args=[str(library_block_data.usage_key)])


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

    # Update content library index synchronously to make sure that search index is updated before
    # the frontend invalidates/refetches index.
    # Currently, this is only required to make sure that removed/discarded components are removed
    # from the search index and displayed to user properly. If it becomes a performance bottleneck
    # for other update operations other than discard, we can update CONTENT_LIBRARY_UPDATED event
    # to include a parameter which can help us decide if the task needs to run sync or async.
    update_content_library_index_docs.apply(args=[str(content_library_data.library_key)])


@receiver(LIBRARY_COLLECTION_CREATED)
@receiver(LIBRARY_COLLECTION_DELETED)
@receiver(LIBRARY_COLLECTION_UPDATED)
@only_if_meilisearch_enabled
def library_collection_updated_handler(**kwargs) -> None:
    """
    Create or update the index for the content library collection
    """
    library_collection = kwargs.get("library_collection", None)
    if not library_collection or not isinstance(library_collection, LibraryCollectionData):  # pragma: no cover
        log.error("Received null or incorrect data for event")
        return

    if library_collection.background:
        update_library_collection_index_doc.delay(
            str(library_collection.library_key),
            library_collection.collection_key,
        )
    else:
        # Update collection index synchronously to make sure that search index is updated before
        # the frontend invalidates/refetches index.
        # See content_library_updated_handler for more details.
        update_library_collection_index_doc.apply(args=[
            str(library_collection.library_key),
            library_collection.collection_key,
        ])


@receiver(CONTENT_OBJECT_ASSOCIATIONS_CHANGED)
@only_if_meilisearch_enabled
def content_object_associations_changed_handler(**kwargs) -> None:
    """
    Update the collections/tags data in the index for the Content Object
    """
    content_object = kwargs.get("content_object", None)
    if not content_object or not isinstance(content_object, ContentObjectChangedData):
        log.error("Received null or incorrect data for event")
        return

    try:
        # Check if valid if course or library block
        usage_key = UsageKey.from_string(str(content_object.object_id))
    except InvalidKeyError:
        try:
            # Check if valid if library collection
            usage_key = LibraryCollectionLocator.from_string(str(content_object.object_id))
        except InvalidKeyError:
            log.error("Received invalid content object id")
            return

    # This event's changes may contain both "tags" and "collections", but this will happen rarely, if ever.
    # So we allow a potential double "upsert" here.
    if not content_object.changes or "tags" in content_object.changes:
        if isinstance(usage_key, LibraryCollectionLocator):
            upsert_collection_tags_index_docs(usage_key)
        else:
            upsert_block_tags_index_docs(usage_key)
    if not content_object.changes or "collections" in content_object.changes:
        upsert_block_collections_index_docs(usage_key)
