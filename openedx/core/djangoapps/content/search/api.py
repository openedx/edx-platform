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
from meilisearch.errors import MeilisearchError
from meilisearch.models.task import TaskInfo
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import LibraryLocatorV2
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
    searchable_doc_for_library_block,
    searchable_doc_tags
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

    status_cb(f"Found {num_courses} courses and {num_libraries} libraries.")
    with _using_temp_index(status_cb) as temp_index_name:
        ############## Configure the index ##############

        # The following index settings are best changed on an empty index.
        # Changing them on a populated index will "re-index all documents in the index, which can take some time"
        # and use more RAM. Instead, we configure an empty index then populate it one course/library at a time.

        # Mark usage_key as unique (it's not the primary key for the index, but nevertheless must be unique):
        client.index(temp_index_name).update_distinct_attribute(Fields.usage_key)
        # Mark which attributes can be used for filtering/faceted search:
        client.index(temp_index_name).update_filterable_attributes([
            Fields.block_type,
            Fields.context_key,
            Fields.org,
            Fields.tags,
            Fields.tags + "." + Fields.tags_taxonomy,
            Fields.tags + "." + Fields.tags_level0,
            Fields.tags + "." + Fields.tags_level1,
            Fields.tags + "." + Fields.tags_level2,
            Fields.tags + "." + Fields.tags_level3,
            Fields.type,
            Fields.access_id,
            Fields.last_published,
        ])
        # Mark which attributes are used for keyword search, in order of importance:
        client.index(temp_index_name).update_searchable_attributes([
            # Keyword search does _not_ search the course name, course ID, breadcrumbs, block type, or other fields.
            Fields.display_name,
            Fields.block_id,
            Fields.content,
            Fields.tags,
            # If we don't list the following sub-fields _explicitly_, they're only sometimes searchable - that is, they
            # are searchable only if at least one document in the index has a value. If we didn't list them here and,
            # say, there were no tags.level3 tags in the index, the client would get an error if trying to search for
            # these sub-fields: "Attribute `tags.level3` is not searchable."
            Fields.tags + "." + Fields.tags_taxonomy,
            Fields.tags + "." + Fields.tags_level0,
            Fields.tags + "." + Fields.tags_level1,
            Fields.tags + "." + Fields.tags_level2,
            Fields.tags + "." + Fields.tags_level3,
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
        for lib_key in lib_keys:
            status_cb(f"{num_contexts_done + 1}/{num_contexts}. Now indexing library {lib_key}")
            docs = []
            for component in lib_api.get_library_components(lib_key):
                try:
                    metadata = lib_api.LibraryXBlockMetadata.from_component(lib_key, component)
                    doc = {}
                    doc.update(searchable_doc_for_library_block(metadata))
                    doc.update(searchable_doc_tags(metadata.usage_key))
                    docs.append(doc)
                except Exception as err:  # pylint: disable=broad-except
                    status_cb(f"Error indexing library component {component}: {err}")
                finally:
                    num_blocks_done += 1
            if docs:
                try:
                    # Add all the docs in this library at once (usually faster than adding one at a time):
                    _wait_for_meili_task(client.index(temp_index_name).add_documents(docs))
                except (TypeError, KeyError, MeilisearchError) as err:
                    status_cb(f"Error indexing library {lib_key}: {err}")

            num_contexts_done += 1

        ############## Courses ##############
        status_cb("Indexing courses...")
        # To reduce memory usage on large instances, split up the CourseOverviews into pages of 1,000 courses:
        paginator = Paginator(CourseOverview.objects.only('id', 'display_name'), 1000)
        for p in paginator.page_range:
            for course in paginator.page(p).object_list:
                status_cb(
                    f"{num_contexts_done + 1}/{num_contexts}. Now indexing course {course.display_name} ({course.id})"
                )
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
                num_contexts_done += 1
                num_blocks_done += len(docs)

    status_cb(f"Done! {num_blocks_done} blocks indexed across {num_contexts_done} courses and libraries.")


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
    current_rebuild_index_name = _get_running_rebuild_index_name()

    client = _get_meilisearch_client()

    tasks = []
    if current_rebuild_index_name:
        # If there is a rebuild in progress, the document will also be deleted from the new index.
        tasks.append(client.index(current_rebuild_index_name).delete_document(meili_id_from_opaque_key(usage_key)))
    tasks.append(client.index(STUDIO_INDEX_NAME).delete_document(meili_id_from_opaque_key(usage_key)))

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
