""" Code to allow indexing content libraries """

import logging
from abc import ABC, abstractmethod

from django.conf import settings
from django.dispatch import receiver
from elasticsearch.exceptions import ConnectionError as ElasticConnectionError
from search.elastic import ElasticSearchEngine, _translate_hits, _process_field_filters, RESERVED_CHARACTERS
from search.search_engine_base import SearchEngine
from opaque_keys.edx.locator import LibraryUsageLocatorV2

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


class ItemNotIndexedException(Exception):
    """
    Item wasn't indexed in ElasticSearch
    """


class SearchIndexerBase(ABC):
    INDEX_NAME = None
    DOCUMENT_TYPE = None
    ENABLE_INDEXING_KEY = None
    SEARCH_KWARGS = {
        # Set this to True or 'wait_for' if immediate refresh is required after any update.
        # See elastic docs for more information.
        'refresh': False
    }

    @classmethod
    @abstractmethod
    def get_item_definition(cls, item):
        """
        Returns a serializable dictionary which can be stored in elasticsearch.
        """

    @classmethod
    def index_items(cls, items):
        """
        Index the specified libraries. If they already exist, replace them with new ones.
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        items = [cls.get_item_definition(item) for item in items]
        return searcher.index(cls.DOCUMENT_TYPE, items, **cls.SEARCH_KWARGS)

    @classmethod
    def search(cls, **kwargs):
        """
        Search the index with the given kwargs
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        response = searcher.search(doc_type=cls.DOCUMENT_TYPE, field_dictionary=kwargs, size=MAX_SIZE)
        return response["results"]

    @classmethod
    def get_items(cls, ids, text_search=None):
        """
        Retrieve a list of items from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        ids_str = [str(i) for i in ids]

        response = searcher.search(
            doc_type=cls.DOCUMENT_TYPE,
            field_dictionary={
                "id": ids_str,
                "schema_version": cls.SCHEMA_VERSION
            },
            size=MAX_SIZE,
        )
        if len(response["results"]) != len(ids_str):
            missing = set(ids_str) - set([result["data"]["id"] for result in response["results"]])
            missing = set(ids_str) - set([result["data"]["id"] for result in response["results"]])
            raise ItemNotIndexedException("Keys not found in index: {}".format(missing))

        if text_search:
            # Elastic is hit twice if text_search is valid
            # Once above to identify unindexed libraries, and now to filter with text_search
            if isinstance(searcher, ElasticSearchEngine):
                response = _translate_hits(searcher._es.search(
                    doc_type=cls.DOCUMENT_TYPE,
                    index=searcher.index_name,
                    body=cls.build_elastic_query(ids_str, text_search),
                    size=MAX_SIZE
                ))
            else:
                response = searcher.search(
                    doc_type=cls.DOCUMENT_TYPE,
                    field_dictionary={"id": ids_str},
                    query_string=text_search,
                    size=MAX_SIZE
                )

        # Search results may not retain the original order of keys - we use this
        # dict to construct a list in the original order of ids
        response_dict = {
            result["data"]["id"]: result["data"]
            for result in response["results"]
        }

        return [
            response_dict[key]
            if key in response_dict
            else None
            for key in ids_str
        ]

    @classmethod
    def remove_items(cls, ids):
        """
        Remove the provided ids from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        ids_str = [str(i) for i in ids]
        searcher.remove(cls.DOCUMENT_TYPE, ids_str, **cls.SEARCH_KWARGS)

    @classmethod
    def remove_all_items(cls):
        """
        Remove all items from the index
        """
        searcher = SearchEngine.get_search_engine(cls.INDEX_NAME)
        response = searcher.search(doc_type=cls.DOCUMENT_TYPE, filter_dictionary={}, size=MAX_SIZE)
        ids = [result["data"]["id"] for result in response["results"]]
        searcher.remove(cls.DOCUMENT_TYPE, ids, **cls.SEARCH_KWARGS)

    @classmethod
    def indexing_is_enabled(cls):
        """
        Checks to see if the indexing feature is enabled
        """
        return settings.FEATURES.get(cls.ENABLE_INDEXING_KEY, False)

    @staticmethod
    def build_elastic_query(ids_str, text_search):
        """
        Build and return an elastic query for doing text search on a library
        """
        # Remove reserved characters (and ") from the text to prevent unexpected errors.
        text_search_normalised = text_search.translate(text_search.maketrans('', '', RESERVED_CHARACTERS + '"'))
        text_search_normalised = text_search.replace('-',' ')
        # Wrap with asterix to enable partial matches
        text_search_normalised = "*{}*".format(text_search_normalised)
        return {
            'query': {
                'filtered': {
                    'query': {
                        'bool': {
                            'should': [
                                {
                                    'query_string': {
                                        'query': text_search_normalised,
                                        "fields": ["content.*"],
                                        "minimum_should_match": "100%",
                                    },
                                },
                                # Add a special wildcard search for id, as it contains a ":" character which is filtered out
                                # in query_string
                                {
                                    'wildcard': {
                                        'id': {
                                            'value': '*{}*'.format(text_search),
                                        }
                                    },
                                },
                            ],
                        },
                    },
                    'filter': {
                        'terms': {
                            'id': ids_str
                        }
                    }
                },
            },
        }


class ContentLibraryIndexer(SearchIndexerBase):
    """
    Class to perform indexing for blockstore-based content libraries
    """

    INDEX_NAME = "content_library_index"
    ENABLE_INDEXING_KEY = "ENABLE_CONTENT_LIBRARY_INDEX"
    DOCUMENT_TYPE = "content_library"
    SCHEMA_VERSION = 0

    @classmethod
    def get_item_definition(cls, library_key):
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
        return {
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
            # only 'content' field is analyzed by elastisearch, and allows text-search
            "content": {
                "id": str(library_key),
                "title": bundle_metadata.title,
                "description": bundle_metadata.description,
            },
        }


class LibraryBlockIndexer(SearchIndexerBase):
    """
    Class to perform indexing on the XBlocks in content libraries.
    """

    INDEX_NAME = "content_library_index"
    ENABLE_INDEXING_KEY = "ENABLE_CONTENT_LIBRARY_INDEX"
    DOCUMENT_TYPE = "content_library_block"
    SCHEMA_VERSION = 0

    @classmethod
    def get_item_definition(cls, usage_key):
        from openedx.core.djangoapps.content_libraries.api import get_block_display_name, _lookup_usage_key

        def_key, lib_bundle = _lookup_usage_key(usage_key)
        is_child = usage_key in lib_bundle.get_bundle_includes().keys()

        # NOTE: Increment ContentLibraryIndexer.SCHEMA_VERSION if the following schema is updated to avoid dealing
        # with outdated indexes which might cause errors due to missing/invalid attributes.
        return {
            "schema_version": ContentLibraryIndexer.SCHEMA_VERSION,
            "id": str(usage_key),
            "library_key": str(lib_bundle.library_key),
            "is_child": is_child,
            "def_key": str(def_key),
            "display_name": get_block_display_name(def_key),
            "block_type": def_key.block_type,
            "has_unpublished_changes": lib_bundle.does_definition_have_unpublished_changes(def_key),
            # only 'content' field is analyzed by elastisearch, and allows text-search
            "content": {
                "id": str(usage_key),
                "display_name": get_block_display_name(def_key),
            },
        }


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
            ContentLibraryIndexer.index_items([library_key])
            if kwargs.get('update_blocks', False):
                blocks = LibraryBlockIndexer.search(library_key=str(library_key))
                usage_keys = [LibraryUsageLocatorV2.from_string(block['data']['id']) for block in blocks]
                LibraryBlockIndexer.index_items(usage_keys)
        except ElasticConnectionError as e:
            log.exception(e)


@receiver(CONTENT_LIBRARY_DELETED)
def remove_library_index(sender, library_key, **kwargs):  # pylint: disable=unused-argument
    """
    Remove from index when library is deleted
    """
    if ContentLibraryIndexer.indexing_is_enabled():
        try:
            ContentLibraryIndexer.remove_items([library_key])
            blocks = LibraryBlockIndexer.search(library_key=str(library_key))
            LibraryBlockIndexer.remove_items([block['data']['id'] for block in blocks])
        except ElasticConnectionError as e:
            log.exception(e)


@receiver(LIBRARY_BLOCK_CREATED)
@receiver(LIBRARY_BLOCK_UPDATED)
def index_block(sender, usage_key, **kwargs):  # pylint: disable=unused-argument
    """
    Index block metadata when created
    """
    if LibraryBlockIndexer.indexing_is_enabled():
        try:
            LibraryBlockIndexer.index_items([usage_key])
        except ConnectionError as e:
            log.exception(e)


@receiver(LIBRARY_BLOCK_DELETED)
def remove_block_index(sender, usage_key, **kwargs):  # pylint: disable=unused-argument
    """
    Remove the block from the index when deleted
    """
    if LibraryBlockIndexer.indexing_is_enabled():
        try:
            LibraryBlockIndexer.remove_items([usage_key])
        except ConnectionError as e:
            log.exception(e)
