"""
Content index and search API using Meilisearch
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Callable, Generator

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.paginator import Paginator
from meilisearch import Client as MeilisearchClient
from meilisearch.errors import MeilisearchApiError, MeilisearchError
from meilisearch.models.task import TaskInfo
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryCollectionLocator
from openedx_learning.api import authoring as authoring_api
from common.djangoapps.student.roles import GlobalStaff
from rest_framework.request import Request
from common.djangoapps.student.role_helpers import get_course_roles
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.search.models import get_access_ids_for_request
from openedx.core.djangoapps.content_libraries import api as lib_api
from xmodule.modulestore.django import modulestore

from .documents import (
    Fields,
    meili_id_from_opaque_key,
    searchable_doc_for_course_block,
    searchable_doc_for_collection,
    searchable_doc_for_library_block,
    searchable_doc_for_usage_key,
    searchable_doc_collections,
    searchable_doc_tags,
    searchable_doc_tags_for_collection,
)

log = logging.getLogger(__name__)

User = get_user_model()

STUDIO_INDEX_SUFFIX = "studio_content"

if hasattr(settings, "MEILISEARCH_INDEX_PREFIX"):
    STUDIO_INDEX_NAME = settings.MEILISEARCH_INDEX_PREFIX + STUDIO_INDEX_SUFFIX
else:
    STUDIO_INDEX_NAME = STUDIO_INDEX_SUFFIX


_MEILI_CLIENT = None
_MEILI_API_KEY_UID = None

LOCK_EXPIRE = 24 * 60 * 60  # Lock expires in 24 hours

MAX_ACCESS_IDS_IN_FILTER = 1_000
MAX_ORGS_IN_FILTER = 1_000

EXCLUDED_XBLOCK_TYPES = ['course', 'course_info']


@contextmanager
def _index_rebuild_lock() -> Generator[str, None, None]:
    """
    Lock to prevent that more than one rebuild is running at the same time
    """
    lock_id = f"lock-meilisearch-index-{STUDIO_INDEX_NAME}"
    new_index_name = STUDIO_INDEX_NAME + "_new"

    status = cache.add(lock_id, new_index_name, LOCK_EXPIRE)

    if not status:
        # Lock already acquired
        raise RuntimeError("Rebuild already in progress")

    # Lock acquired
    try:
        yield new_index_name
    finally:
        # Release the lock
        cache.delete(lock_id)


def _get_running_rebuild_index_name() -> str | None:
    lock_id = f"lock-meilisearch-index-{STUDIO_INDEX_NAME}"

    return cache.get(lock_id)


def _get_meilisearch_client():
    """
    Get the Meiliesearch client
    """
    global _MEILI_CLIENT  # pylint: disable=global-statement

    # Connect to Meilisearch
    if not is_meilisearch_enabled():
        raise RuntimeError("MEILISEARCH_ENABLED is not set - search functionality disabled.")

    if _MEILI_CLIENT is not None:
        return _MEILI_CLIENT

    _MEILI_CLIENT = MeilisearchClient(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
    try:
        _MEILI_CLIENT.health()
    except MeilisearchError as err:
        _MEILI_CLIENT = None
        raise ConnectionError("Unable to connect to Meilisearch") from err
    return _MEILI_CLIENT


def clear_meilisearch_client():
    global _MEILI_CLIENT  # pylint: disable=global-statement

    _MEILI_CLIENT = None


def _get_meili_api_key_uid():
    """
    Helper method to get the UID of the API key we're using for Meilisearch
    """
    global _MEILI_API_KEY_UID  # pylint: disable=global-statement
    if _MEILI_API_KEY_UID is None:
        _MEILI_API_KEY_UID = _get_meilisearch_client().get_key(settings.MEILISEARCH_API_KEY).uid
    return _MEILI_API_KEY_UID


def _wait_for_meili_task(info: TaskInfo) -> None:
    """
    Simple helper method to wait for a Meilisearch task to complete
    This method will block until the task is completed, so it should only be used in celery tasks
    or management commands.
    """
    client = _get_meilisearch_client()
    current_status = client.get_task(info.task_uid)
    while current_status.status in ("enqueued", "processing"):
        time.sleep(0.5)
        current_status = client.get_task(info.task_uid)
    if current_status.status != "succeeded":
        try:
            err_reason = current_status.error['message']
        except (TypeError, KeyError):
            err_reason = "Unknown error"
        raise MeilisearchError(err_reason)


def _wait_for_meili_tasks(info_list: list[TaskInfo]) -> None:
    """
    Simple helper method to wait for multiple Meilisearch tasks to complete
    """
    while info_list:
        info = info_list.pop()
        _wait_for_meili_task(info)


def _index_exists(index_name: str) -> bool:
    """
    Check if an index exists
    """
    client = _get_meilisearch_client()
    try:
        client.get_index(index_name)
    except MeilisearchError as err:
        if err.code == "index_not_found":
            return False
        else:
            raise err
    return True


@contextmanager
def _using_temp_index(status_cb: Callable[[str], None] | None = None) -> Generator[str, None, None]:
    """
    Create a new temporary Meilisearch index, populate it, then swap it to
    become the active index.

    Args:
        status_cb (Callable): A callback function to report status messages
    """
    if status_cb is None:
        status_cb = log.info

    client = _get_meilisearch_client()
    status_cb("Checking index...")
    with _index_rebuild_lock() as temp_index_name:
        if _index_exists(temp_index_name):
            status_cb("Temporary index already exists. Deleting it...")
            _wait_for_meili_task(client.delete_index(temp_index_name))

        status_cb("Creating new index...")
        _wait_for_meili_task(
            client.create_index(temp_index_name, {'primaryKey': 'id'})
        )
        new_index_created = client.get_index(temp_index_name).created_at

        yield temp_index_name

        if not _index_exists(STUDIO_INDEX_NAME):
            # We have to create the "target" index before we can successfully swap the new one into it:
            status_cb("Preparing to swap into index (first time)...")
            _wait_for_meili_task(client.create_index(STUDIO_INDEX_NAME))
        status_cb("Swapping index...")
        client.swap_indexes([{'indexes': [temp_index_name, STUDIO_INDEX_NAME]}])
        # If we're using an API key that's restricted to certain index prefix(es), we won't be able to get the status
        # of this request unfortunately. https://github.com/meilisearch/meilisearch/issues/4103
        while True:
            time.sleep(1)
            if client.get_index(STUDIO_INDEX_NAME).created_at != new_index_created:
                status_cb("Waiting for swap completion...")
            else:
                break
        status_cb("Deleting old index...")
        _wait_for_meili_task(client.delete_index(temp_index_name))


def _recurse_children(block, fn, status_cb: Callable[[str], None] | None = None) -> None:
    """
    Recurse the children of an XBlock and call the given function for each

    The main purpose of this is just to wrap the loading of each child in
    try...except. Otherwise block.get_children() would do what we need.
    """
    if block.has_children:
        for child_id in block.children:
            try:
                child = block.get_child(child_id)
            except Exception as err:  # pylint: disable=broad-except
                log.exception(err)
                if status_cb is not None:
                    status_cb(f"Unable to load block {child_id}")
            else:
                fn(child)


def _update_index_docs(docs) -> None:
    """
    Helper function that updates the documents in the search index

    If there is a rebuild in progress, the document will also be added to the new index.
    """
    if not docs:
        return

    client = _get_meilisearch_client()
    current_rebuild_index_name = _get_running_rebuild_index_name()

    tasks = []
    if current_rebuild_index_name:
        # If there is a rebuild in progress, the document will also be added to the new index.
        tasks.append(client.index(current_rebuild_index_name).update_documents(docs))
    tasks.append(client.index(STUDIO_INDEX_NAME).update_documents(docs))

    _wait_for_meili_tasks(tasks)


def only_if_meilisearch_enabled(f):
    """
    Only call `f` if meilisearch is enabled
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        """Wraps the decorated function."""
        if is_meilisearch_enabled():
            return f(*args, **kwargs)
    return wrapper


def is_meilisearch_enabled() -> bool:
    """
    Returns whether Meilisearch is enabled
    """
    if hasattr(settings, "MEILISEARCH_ENABLED"):
        return settings.MEILISEARCH_ENABLED

    return False


# pylint: disable=too-many-statements
def rebuild_index(status_cb: Callable[[str], None] | None = None) -> None:
    """
    Rebuild the Meilisearch index from scratch
    """
    if status_cb is None:
        status_cb = log.info

    client = _get_meilisearch_client()
    store = modulestore()

    # Get the lists of libraries
    status_cb("Counting libraries...")
    lib_keys = [lib.library_key for lib in lib_api.ContentLibrary.objects.select_related('org').only('org', 'slug')]
    num_libraries = len(lib_keys)

    # Get the list of courses
    status_cb("Counting courses...")
    num_courses = CourseOverview.objects.count()

    # Some counters so we can track our progress as indexing progresses:
    num_contexts = num_courses + num_libraries
    num_contexts_done = 0  # How many courses/libraries we've indexed
    num_blocks_done = 0  # How many individual components/XBlocks we've indexed

    status_cb(f"Found {num_courses} courses, {num_libraries} libraries.")
    with _using_temp_index(status_cb) as temp_index_name:
        ############## Configure the index ##############

        # The following index settings are best changed on an empty index.
        # Changing them on a populated index will "re-index all documents in the index, which can take some time"
        # and use more RAM. Instead, we configure an empty index then populate it one course/library at a time.

        # Mark usage_key as unique (it's not the primary key for the index, but nevertheless must be unique):
        client.index(temp_index_name).update_distinct_attribute(Fields.usage_key)
        # Mark which attributes can be used for filtering/faceted search:
        client.index(temp_index_name).update_filterable_attributes([
            # Get specific block/collection using combination of block_id and context_key
            Fields.block_id,
            Fields.block_type,
            Fields.context_key,
            Fields.usage_key,
            Fields.org,
            Fields.tags,
            Fields.tags + "." + Fields.tags_taxonomy,
            Fields.tags + "." + Fields.tags_level0,
            Fields.tags + "." + Fields.tags_level1,
            Fields.tags + "." + Fields.tags_level2,
            Fields.tags + "." + Fields.tags_level3,
            Fields.collections,
            Fields.collections + "." + Fields.collections_display_name,
            Fields.collections + "." + Fields.collections_key,
            Fields.type,
            Fields.access_id,
            Fields.last_published,
            Fields.content + "." + Fields.problem_types,
        ])
        # Mark which attributes are used for keyword search, in order of importance:
        client.index(temp_index_name).update_searchable_attributes([
            # Keyword search does _not_ search the course name, course ID, breadcrumbs, block type, or other fields.
            Fields.display_name,
            Fields.block_id,
            Fields.content,
            Fields.description,
            Fields.tags,
            Fields.collections,
            # If we don't list the following sub-fields _explicitly_, they're only sometimes searchable - that is, they
            # are searchable only if at least one document in the index has a value. If we didn't list them here and,
            # say, there were no tags.level3 tags in the index, the client would get an error if trying to search for
            # these sub-fields: "Attribute `tags.level3` is not searchable."
            Fields.tags + "." + Fields.tags_taxonomy,
            Fields.tags + "." + Fields.tags_level0,
            Fields.tags + "." + Fields.tags_level1,
            Fields.tags + "." + Fields.tags_level2,
            Fields.tags + "." + Fields.tags_level3,
            Fields.collections + "." + Fields.collections_display_name,
            Fields.collections + "." + Fields.collections_key,
        ])
        # Mark which attributes can be used for sorting search results:
        client.index(temp_index_name).update_sortable_attributes([
            Fields.display_name,
            Fields.created,
            Fields.modified,
            Fields.last_published,
        ])

        # Update the search ranking rules to let the (optional) "sort" parameter take precedence over keyword relevance.
        # cf https://www.meilisearch.com/docs/learn/core_concepts/relevancy
        client.index(temp_index_name).update_ranking_rules([
            "sort",
            "words",
            "typo",
            "proximity",
            "attribute",
            "exactness",
        ])

        ############## Libraries ##############
        status_cb("Indexing libraries...")

        def index_library(lib_key: str) -> list:
            docs = []
            for component in lib_api.get_library_components(lib_key):
                try:
                    metadata = lib_api.LibraryXBlockMetadata.from_component(lib_key, component)
                    doc = {}
                    doc.update(searchable_doc_for_library_block(metadata))
                    doc.update(searchable_doc_tags(metadata.usage_key))
                    doc.update(searchable_doc_collections(metadata.usage_key))
                    docs.append(doc)
                except Exception as err:  # pylint: disable=broad-except
                    status_cb(f"Error indexing library component {component}: {err}")
            if docs:
                try:
                    # Add all the docs in this library at once (usually faster than adding one at a time):
                    _wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                except (TypeError, KeyError, MeilisearchError) as err:
                    status_cb(f"Error indexing library {lib_key}: {err}")
            return docs

        ############## Collections ##############
        def index_collection_batch(batch, num_done, library_key) -> int:
            docs = []
            for collection in batch:
                try:
                    doc = searchable_doc_for_collection(library_key, collection.key, collection=collection)
                    doc.update(searchable_doc_tags_for_collection(library_key, collection.key))
                    docs.append(doc)
                except Exception as err:  # pylint: disable=broad-except
                    status_cb(f"Error indexing collection {collection}: {err}")
                num_done += 1

            if docs:
                try:
                    # Add docs in batch of 100 at once (usually faster than adding one at a time):
                    _wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                except (TypeError, KeyError, MeilisearchError) as err:
                    status_cb(f"Error indexing collection batch {p}: {err}")
            return num_done

        for lib_key in lib_keys:
            status_cb(f"{num_contexts_done + 1}/{num_contexts}. Now indexing blocks in library {lib_key}")
            lib_docs = index_library(lib_key)
            num_blocks_done += len(lib_docs)

            # To reduce memory usage on large instances, split up the Collections into pages of 100 collections:
            library = lib_api.get_library(lib_key)
            collections = authoring_api.get_collections(library.learning_package.id, enabled=True)
            num_collections = collections.count()
            num_collections_done = 0
            status_cb(f"{num_collections_done + 1}/{num_collections}. Now indexing collections in library {lib_key}")
            paginator = Paginator(collections, 100)
            for p in paginator.page_range:
                num_collections_done = index_collection_batch(
                    paginator.page(p).object_list,
                    num_collections_done,
                    lib_key,
                )
            status_cb(f"{num_collections_done}/{num_collections} collections indexed for library {lib_key}")

            num_contexts_done += 1

        ############## Courses ##############
        status_cb("Indexing courses...")
        # To reduce memory usage on large instances, split up the CourseOverviews into pages of 1,000 courses:

        def index_course(course: CourseOverview) -> list:
            docs = []
            # Pre-fetch the course with all of its children:
            course = store.get_course(course.id, depth=None)

            def add_with_children(block):
                """ Recursively index the given XBlock/component """
                doc = searchable_doc_for_course_block(block)
                doc.update(searchable_doc_tags(block.usage_key))
                docs.append(doc)  # pylint: disable=cell-var-from-loop
                _recurse_children(block, add_with_children)  # pylint: disable=cell-var-from-loop

            # Index course children
            _recurse_children(course, add_with_children)

            if docs:
                # Add all the docs in this course at once (usually faster than adding one at a time):
                _wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
            return docs

        paginator = Paginator(CourseOverview.objects.only('id', 'display_name'), 1000)
        for p in paginator.page_range:
            for course in paginator.page(p).object_list:
                status_cb(
                    f"{num_contexts_done + 1}/{num_contexts}. Now indexing course {course.display_name} ({course.id})"
                )
                course_docs = index_course(course)
                num_contexts_done += 1
                num_blocks_done += len(course_docs)

    status_cb(f"Done! {num_blocks_done} blocks indexed across {num_contexts_done} courses, collections and libraries.")


def upsert_xblock_index_doc(usage_key: UsageKey, recursive: bool = True) -> None:
    """
    Creates or updates the document for the given XBlock in the search index


    Args:
        usage_key (UsageKey): The usage key of the XBlock to index
        recursive (bool): If True, also index all children of the XBlock
    """
    xblock = modulestore().get_item(usage_key)
    xblock_type = xblock.scope_ids.block_type

    if xblock_type in EXCLUDED_XBLOCK_TYPES:
        return

    docs = []

    def add_with_children(block):
        """ Recursively index the given XBlock/component """
        doc = searchable_doc_for_course_block(block)
        docs.append(doc)
        if recursive:
            _recurse_children(block, add_with_children)

    add_with_children(xblock)

    _update_index_docs(docs)


def delete_index_doc(usage_key: UsageKey) -> None:
    """
    Deletes the document for the given XBlock from the search index

    Args:
        usage_key (UsageKey): The usage key of the XBlock to be removed from the index
    """
    doc = searchable_doc_for_usage_key(usage_key)
    _delete_index_doc(doc[Fields.id])


def _delete_index_doc(doc_id) -> None:
    """
    Helper function that deletes the document with the given ID from the search index

    If there is a rebuild in progress, the document will also be removed from the new index.
    """
    if not doc_id:
        return

    client = _get_meilisearch_client()
    current_rebuild_index_name = _get_running_rebuild_index_name()

    tasks = []
    if current_rebuild_index_name:
        # If there is a rebuild in progress, the document will also be removed from the new index.
        tasks.append(client.index(current_rebuild_index_name).delete_document(doc_id))

    tasks.append(client.index(STUDIO_INDEX_NAME).delete_document(doc_id))

    _wait_for_meili_tasks(tasks)


def delete_all_draft_docs_for_library(library_key: LibraryLocatorV2) -> None:
    """
    Deletes draft documents for the given XBlocks from the search index
    """
    current_rebuild_index_name = _get_running_rebuild_index_name()
    client = _get_meilisearch_client()
    # Delete all documents where last_published is null i.e. never published before.
    delete_filter = [
        f'{Fields.context_key}="{library_key}"',
        # This field should only be NULL or have a value, but we're also checking IS EMPTY just in case.
        # Inner arrays are connected by an OR
        [f'{Fields.last_published} IS EMPTY', f'{Fields.last_published} IS NULL'],
    ]

    tasks = []
    if current_rebuild_index_name:
        # If there is a rebuild in progress, the documents will also be deleted from the new index.
        tasks.append(client.index(current_rebuild_index_name).delete_documents(filter=delete_filter))
    tasks.append(client.index(STUDIO_INDEX_NAME).delete_documents(filter=delete_filter))

    _wait_for_meili_tasks(tasks)


def upsert_library_block_index_doc(usage_key: UsageKey) -> None:
    """
    Creates or updates the document for the given Library Block in the search index
    """

    library_block = lib_api.get_component_from_usage_key(usage_key)
    library_block_metadata = lib_api.LibraryXBlockMetadata.from_component(usage_key.context_key, library_block)

    docs = [
        searchable_doc_for_library_block(library_block_metadata)
    ]

    _update_index_docs(docs)


def _get_document_from_index(document_id: str) -> dict:
    """
    Returns the Document identified by the given ID, from the given index.

    Returns None if the document or index do not exist.
    """
    client = _get_meilisearch_client()
    document = None
    index_name = STUDIO_INDEX_NAME
    try:
        index = client.get_index(index_name)
        document = index.get_document(document_id)
    except (MeilisearchError, MeilisearchApiError) as err:
        # The index or document doesn't exist
        log.warning(f"Unable to fetch document {document_id} from {index_name}: {err}")

    return document


def upsert_library_collection_index_doc(library_key: LibraryLocatorV2, collection_key: str) -> None:
    """
    Creates, updates, or deletes the document for the given Library Collection in the search index.

    If the Collection is not found or disabled (i.e. soft-deleted), then delete it from the search index.
    """
    doc = searchable_doc_for_collection(library_key, collection_key)
    update_components = False

    # Soft-deleted/disabled collections are removed from the index
    # and their components updated.
    if doc.get('_disabled'):

        _delete_index_doc(doc[Fields.id])

        update_components = True

    # Hard-deleted collections are also deleted from the index,
    # but their components are automatically updated as part of the deletion process, so we don't have to.
    elif not doc.get(Fields.type):

        _delete_index_doc(doc[Fields.id])

    # Otherwise, upsert the collection.
    # Newly-added/restored collection get their components updated too.
    else:
        already_indexed = _get_document_from_index(doc[Fields.id])
        if not already_indexed:
            update_components = True

        _update_index_docs([doc])

    # Asynchronously update the collection's components "collections" field
    if update_components:
        from .tasks import update_library_components_collections as update_task

        update_task.delay(str(library_key), collection_key)


def update_library_components_collections(
    library_key: LibraryLocatorV2,
    collection_key: str,
    batch_size: int = 1000,
) -> None:
    """
    Updates the "collections" field for all components associated with a given Library Collection.

    Because there may be a lot of components, we send these updates to Meilisearch in batches.
    """
    library = lib_api.get_library(library_key)
    components = authoring_api.get_collection_components(library.learning_package.id, collection_key)

    paginator = Paginator(components, batch_size)
    for page in paginator.page_range:
        docs = []

        for component in paginator.page(page).object_list:
            usage_key = lib_api.library_component_usage_key(
                library_key,
                component,
            )
            doc = searchable_doc_collections(usage_key)
            docs.append(doc)

        log.info(
            f"Updating document.collections for library {library_key} components"
            f" page {page} / {paginator.num_pages}"
        )
        _update_index_docs(docs)


def upsert_content_library_index_docs(library_key: LibraryLocatorV2) -> None:
    """
    Creates or updates the documents for the given Content Library in the search index
    """
    docs = []
    for component in lib_api.get_library_components(library_key):
        metadata = lib_api.LibraryXBlockMetadata.from_component(library_key, component)
        doc = searchable_doc_for_library_block(metadata)
        docs.append(doc)

    _update_index_docs(docs)


def upsert_block_tags_index_docs(usage_key: UsageKey):
    """
    Updates the tags data in documents for the given Course/Library block
    """
    doc = {Fields.id: meili_id_from_opaque_key(usage_key)}
    doc.update(searchable_doc_tags(usage_key))
    _update_index_docs([doc])


def upsert_block_collections_index_docs(usage_key: UsageKey):
    """
    Updates the collections data in documents for the given Course/Library block
    """
    doc = {Fields.id: meili_id_from_opaque_key(usage_key)}
    doc.update(searchable_doc_collections(usage_key))
    _update_index_docs([doc])


def upsert_collection_tags_index_docs(collection_usage_key: LibraryCollectionLocator):
    """
    Updates the tags data in documents for the given library collection
    """

    doc = searchable_doc_tags_for_collection(collection_usage_key.library_key, collection_usage_key.collection_id)
    _update_index_docs([doc])


def _get_user_orgs(request: Request) -> list[str]:
    """
    Get the org.short_names for the organizations that the requesting user has OrgStaffRole or OrgInstructorRole.

    Note: org-level roles have course_id=None to distinguish them from course-level roles.
    """
    course_roles = get_course_roles(request.user)
    return list(set(
        role.org
        for role in course_roles
        if role.course_id is None and role.role in ['staff', 'instructor']
    ))


def _get_meili_access_filter(request: Request) -> dict:
    """
    Return meilisearch filter based on the requesting user's permissions.
    """
    # Global staff can see anything, so no filters required.
    if GlobalStaff().has_user(request.user):
        return {}

    # Everyone else is limited to their org staff roles...
    user_orgs = _get_user_orgs(request)[:MAX_ORGS_IN_FILTER]

    # ...or the N most recent courses and libraries they can access.
    access_ids = get_access_ids_for_request(request, omit_orgs=user_orgs)[:MAX_ACCESS_IDS_IN_FILTER]
    return {
        "filter": f"org IN {user_orgs} OR access_id IN {access_ids}",
    }


def generate_user_token_for_studio_search(request):
    """
    Returns a Meilisearch API key that only allows the user to search content that they have permission to view
    """
    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=7)

    search_rules = {
        STUDIO_INDEX_NAME: _get_meili_access_filter(request),
    }
    # Note: the following is just generating a JWT. It doesn't actually make an API call to Meilisearch.
    restricted_api_key = _get_meilisearch_client().generate_tenant_token(
        api_key_uid=_get_meili_api_key_uid(),
        search_rules=search_rules,
        expires_at=expires_at,
    )

    return {
        "url": settings.MEILISEARCH_PUBLIC_URL,
        "index_name": STUDIO_INDEX_NAME,
        "api_key": restricted_api_key,
    }
