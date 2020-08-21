""" Code to allow indexing content libraries """

import logging

from django.conf import settings
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from search.search_engine_base import SearchEngine

from openedx.core.djangoapps.content_libraries.constants import DRAFT_NAME
from openedx.core.djangoapps.content_libraries.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_UPDATED,
    CONTENT_LIBRARY_DELETED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_UPDATED,
    LIBRARY_BLOCK_DELETED,
)
from openedx.core.djangoapps.content_libraries.library_bundle import LibraryBundle
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from openedx.core.lib.blockstore_api import get_bundle

log = logging.getLogger(__name__)

MAX_SIZE = 10000  # 10000 is the maximum records elastic is able to return in a single result. Defaults to 10.


class LibraryNotIndexedException(Exception):
    """
    Library supplied wasn't indexed in ElasticSearch
    """


class ContentLibraryIndexer:
    """
    Class to perform indexing for blockstore-based content libraries
    """

    INDEX_NAME = "content_library_index"
    LIBRARY_DOCUMENT_TYPE = "content_library"

    SCHEMA_VERSION = 0

    @classmethod
    def index_libraries(cls, library_keys):
        """
        Index the specified libraries. If they already exist, replace them with new ones.
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)

        library_dicts = []

        for library_key in library_keys:
            ref = ContentLibrary.objects.get_by_key(library_key)
            lib_bundle = LibraryBundle(library_key, ref.bundle_uuid, draft_name=DRAFT_NAME)
            num_blocks = len(lib_bundle.get_top_level_usages())
            last_published = lib_bundle.get_last_published_time()
            last_published_str = None
            if last_published:
                last_published_str = last_published.strftime('%Y-%m-%dT%H:%M:%SZ')
            (has_unpublished_changes, has_unpublished_deletes) = lib_bundle.has_changes()

            bundle_metadata = get_bundle(ref.bundle_uuid)

            # NOTE: Increment ContentLibraryIndexer.SCHEMA_VERSION if the following schema is updated to avoid dealing
            # with outdated indexes which might cause errors due to missing/invalid attributes.
            library_dict = {
                "schema_version": ContentLibraryIndexer.SCHEMA_VERSION,
                "id": str(library_key),
                "uuid": str(bundle_metadata.uuid),
                "title": bundle_metadata.title,
                "description": bundle_metadata.description,
                "num_blocks": num_blocks,
                "version": bundle_metadata.latest_version,
                "last_published": last_published_str,
                "has_unpublished_changes": has_unpublished_changes,
                "has_unpublished_deletes": has_unpublished_deletes,
            }
            library_dicts.append(library_dict)

        return searcher.index(cls.LIBRARY_DOCUMENT_TYPE, library_dicts)

    @classmethod
    def get_libraries(cls, library_keys):
        """
        Retrieve a list of libraries from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        library_keys_str = [str(key) for key in library_keys]
        response = searcher.search(
            doc_type=cls.LIBRARY_DOCUMENT_TYPE,
            field_dictionary={
                "id": library_keys_str,
                "schema_version": ContentLibraryIndexer.SCHEMA_VERSION
            },
            size=MAX_SIZE,
        )

        # Search results may not retain the original order of keys - we use this
        # dict to construct a list in the original order of library_keys
        response_dict = {
            result["data"]["id"]: result["data"]
            for result in response["results"]
        }
        if len(response_dict) != len(library_keys_str):
            missing = set(library_keys_str) - set(response_dict.keys())
            raise LibraryNotIndexedException("Keys not found in index: {}".format(missing))
        return [
            response_dict[key]
            for key in library_keys_str
        ]

    @classmethod
    def remove_libraries(cls, library_keys):
        """
        Remove the provided library_keys from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        ids_str = [str(key) for key in library_keys]
        searcher.remove(cls.LIBRARY_DOCUMENT_TYPE, ids_str)

    @classmethod
    def remove_all_libraries(cls):
        """
        Remove all libraries from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        response = searcher.search(doc_type=cls.LIBRARY_DOCUMENT_TYPE, filter_dictionary={}, size=MAX_SIZE)
        ids = [result["data"]["id"] for result in response["results"]]
        searcher.remove(cls.LIBRARY_DOCUMENT_TYPE, ids)

    @classmethod
    def indexing_is_enabled(cls):
        """
        Checks to see if the indexing feature is enabled
        """
        return settings.FEATURES.get("ENABLE_CONTENT_LIBRARY_INDEX", False)


@receiver(CONTENT_LIBRARY_CREATED)
@receiver(CONTENT_LIBRARY_UPDATED)
@receiver(LIBRARY_BLOCK_CREATED)
@receiver(LIBRARY_BLOCK_UPDATED)
@receiver(LIBRARY_BLOCK_DELETED)
def index_library(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Index library when created or updated, or when its blocks are modified.
    """
    if ContentLibraryIndexer.indexing_is_enabled():
        try:
            ContentLibraryIndexer.index_libraries([library_key])
        except ElasticConnectionError as e:
            log.exception(e)


@receiver(CONTENT_LIBRARY_DELETED)
def remove_library_index(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Remove from index when library is deleted
    """
    if ContentLibraryIndexer.indexing_is_enabled():
        try:
            ContentLibraryIndexer.remove_libraries([library_key])
        except ElasticConnectionError as e:
            log.exception(e)
