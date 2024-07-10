"""
Meilisearch implementation for courseware search index
"""
import copy
import hashlib
import logging
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from meilisearch import Client, errors
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from search.search_engine_base import SearchEngine
from search.utils import ValueRange, _is_iterable

# log appears to be standard name used for logger
log = logging.getLogger(__name__)

prefix = getattr(settings, "MEILISEARCH_INDEX_PREFIX", "")
RESERVED_CHARACTERS = "+=><!(){}[]^~*:\\/&|?"
INDEX_SETTINGS = {
    f"{prefix}library_index": {
        "filterableAttributes": [
            "library",
            "id"
        ],
        "facets": [
            "library"
        ]
    },
    f"{prefix}courseware_content": {
        "filterableAttributes": [
            "id",
            "course",
            "org"
        ],
        "facets": [
            "org"
        ]
    },
    f"{prefix}course_info": {
        "filterableAttributes": [
            "id",
            "org",
            "course",
            "start",
            "enrollment_start"
        ],
        "facets": [
            "org",
        ]
    },
}


def sanitize_id(_id: str | int) -> str:
    return hashlib.md5(f"{_id}".encode('utf-8')).hexdigest()


def sanitized_id(source: dict, create_usage_key=True) -> dict:
    """
    Sanitize the Id key to avoid restricted objects
    :param source:
    :param create_usage_key:
    :return:
    """
    if "id" not in source:
        return source

    try:
        usage_key = UsageKey.from_string(source['id'])
        if create_usage_key:
            source["usage_key"] = source["id"]
        source["id"] = usage_key.block_id
    except (Exception, InvalidKeyError) as ex:  # pylint: disable=broad-except
        source["id"] = sanitize_id(source["id"])
        log.info(f"{str(ex)} - {source['id']} - {type(ex)}")

    return source


def build_filter(key, val):
    """
    This function is making meilisearch compatible filters
    :param key: name of attribute
    :param val: value of attribute
    :return:
    """
    if isinstance(val, list):
        if len(val) == 2 and type(val[0]) in (datetime, type(None)) and type(val[1]) in (datetime, type(None)):
            f = ""
            if val[0]:
                f += f"{str(key).lower()} > \"{val[0].isoformat(timespec='milliseconds')}\""
            if val[1]:
                f += f" and {str(key).lower()} >= \"{val[1].isoformat(timespec='milliseconds')}\""
            return f"({f})"

    elif isinstance(val, dict):
        log.info('Dict Filter Not Handled')
    return f"{str(key).lower()}='{val}'"


def filter_builder(_filters: list[dict]) -> list[str]:
    """
    Create meilisearch compatible filter queries
    :param _filters:
    :return:
    """
    if not _filters:
        return []
    str_filters = []

    for f in _filters:
        if "id" in f:
            f.update(**sanitized_id(f.copy(), create_usage_key=False))
        for key, val in f.items():
            str_filters.append(build_filter(key, val))
    return [
        " OR ".join(str_filters)
    ]


def serialize_datetimes(source):
    """
    Recursively convert all datetime objects in a dictionary to strings.
    """
    if isinstance(source.get("id"), str):
        source.update(**sanitized_id(source.copy()))

    for key, value in source.items():
        if isinstance(value, datetime):
            source[key] = value.isoformat()
        elif isinstance(value, dict):
            serialize_datetimes(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, datetime):
                    item = item.isoformat()
                elif isinstance(item, dict):
                    serialize_datetimes(item)
    return source


def _translate_hits(ms_response):
    """
    Provide result set in our desired format from Meilisearch results.
    """

    def translate_result(result):
        """
        Any conversion from Meilisearch result syntax into our search engine syntax
        """
        translated_result = copy.copy(result)
        translated_result["data"] = {**translated_result}
        translated_result["score"] = translated_result.pop("_score", 1.0)
        return translated_result

    results = list(map(translate_result, ms_response["hits"]))
    response = {
        "took": ms_response["processingTimeMs"],
        "total": ms_response["estimatedTotalHits"],
        "max_score": max(result["score"] for result in results) if results else None,
        "results": results,
    }
    if "facetDistribution" in ms_response:
        aggs = {}
        for key, terms in ms_response["facetDistribution"].items():
            aggs[key] = {"terms": terms}
        response["aggs"] = aggs

    return response


def _get_filter_field(field_name, field_value):
    """
    Return field to apply into filter.
    """
    filter_query_field = {field_name: field_value}
    if isinstance(field_value, ValueRange):
        filter_query_field = {
            field_name: [field_value.lower, field_value.upper]
        }
    elif _is_iterable(field_value):
        filter_query_field = {
            field_name: field_value,
        }
    return filter_query_field


def _process_field_queries(field_dictionary):
    """
    Prepare Meilisearch query which must be in the Meilisearch record set.
    """
    return [
        _get_filter_field(field, field_value)
        for field, field_value in field_dictionary.items()
    ]


def _process_filters(filter_dictionary):
    """
    Build list for filtering.
    """
    for field, value in filter_dictionary.items():
        if value:
            yield _get_filter_field(field, value)


def _process_exclude_dictionary(exclude_dictionary):
    """
    Build a list of term fields which will be excluded from result set.
    """
    for exclude_property, exclude_values in exclude_dictionary.items():
        if not isinstance(exclude_values, list):
            exclude_values = (exclude_values,)
        yield from (
            {exclude_property: exclude_value}
            for exclude_value in exclude_values
        )


def _process_aggregation_terms(aggregation_terms):
    """
    Meilisearch does not support aggregations natively as Elasticsearch.
    """
    return aggregation_terms


class MeiliSearchEngine(SearchEngine):
    """
    Meilisearch implementation of SearchEngine abstraction
    """
    backend_name = "meilisearch"

    @staticmethod
    def get_cache_item_name(index_name):
        """
        Name-formatter for cache_item_name
        """
        return f"meili_search_mappings_{index_name}"

    @classmethod
    def get_mappings(cls, index_name):
        """
        Fetch mapped-items structure from cache
        """
        return cache.get(cls.get_cache_item_name(index_name), {})

    @classmethod
    def set_mappings(cls, index_name, mappings):
        """
        Set new mapped-items structure into cache
        """
        cache.set(cls.get_cache_item_name(index_name), mappings)

    @property
    def mappings(self):
        """
        Get mapping of current index.

        Mappings format in Meilisearch is different from Elasticsearch.
        """
        mapping = MeiliSearchEngine.get_mappings(self._prefixed_index_name)
        if not mapping:
            # Assuming Meilisearch mappings are pre-defined elsewhere
            mapping = {}  # Update this if there's a way to fetch mappings
            if mapping:
                MeiliSearchEngine.set_mappings(self._prefixed_index_name, mapping)
        return mapping

    def _clear_mapping(self):
        """
        Remove the cached mappings.
        """
        MeiliSearchEngine.set_mappings(self._prefixed_index_name, {})

    def __init__(self, index=None, options=None):
        super().__init__(index)
        MEILISEARCH_URL = getattr(settings, "MEILISEARCH_URL", 'http://127.0.0.1:7700')
        MEILISEARCH_API_KEY = getattr(settings, "MEILISEARCH_API_KEY", "masterKey")
        self._ms = Client(MEILISEARCH_URL, MEILISEARCH_API_KEY)
        self._index = self._ms.index(self._prefixed_index_name)
        # Ensure index exists
        try:
            self._index.fetch_info()
        except errors.MeilisearchApiError:
            self._ms.create_index(self._prefixed_index_name, options=options)
            self.update_settings()

    @property
    def _prefixed_index_name(self):
        """
        Property that returns the defined index_name with the configured prefix.
        """
        return prefix + self.index_name

    def _check_mappings(self, body):
        """
        Meilisearch doesn't require explicit mappings like Elasticsearch.
        """

    def index(self, sources, **kwargs):
        """
        Implements call to add documents to the Meilisearch index.
        """
        try:
            serialized_sources = list(map(serialize_datetimes, sources))
            self._index.add_documents(serialized_sources, primary_key='id')
        except errors.MeilisearchApiError as ex:
            log.exception("Error during Meilisearch bulk operation.")
            raise

    def remove(self, doc_ids, **kwargs):
        """
        Implements call to remove the documents from the index.
        """
        try:
            for doc_id in doc_ids:
                log.debug("Removing document with id %s", doc_id)
                self._index.delete_document(doc_id)
        except errors.MeilisearchApiError as ex:
            log.exception("An error occurred while removing documents from the index.")
            raise

    def search(self,
               query_string=None,
               field_dictionary=None,
               filter_dictionary=None,
               exclude_dictionary=None,
               aggregation_terms=None,
               exclude_ids=None,
               use_field_match=False,
               log_search_params=False,
               **kwargs):
        """
        Implements call to search the index for the desired content.
        """

        log.debug("searching index with %s", query_string)
        filters = []
        filterables = INDEX_SETTINGS.get(self._prefixed_index_name, {}).get('filterableAttributes', [])

        if query_string:
            query_string = query_string.translate(
                query_string.maketrans("", "", RESERVED_CHARACTERS)
            )

        if field_dictionary:
            filters.extend(filter_builder(_process_field_queries(field_dictionary)))

        if filter_dictionary:
            filter_dictionary = {
                fl: filter_dictionary.get(fl, None) for fl in filterables if
                filter_dictionary.get(fl, None)
            }
            filters.extend(filter_builder(_process_filters(filter_dictionary)))

        search_params = {
            "filter": filters,
            "facets": INDEX_SETTINGS.get(self._prefixed_index_name, {}).get('facets', [])
        }
        if log_search_params:
            log.info(f"full meili search body {search_params}")

        try:
            ms_response = self._index.search(query_string, search_params)
        except errors.MeilisearchApiError as ex:
            log.exception("error while searching index - %r", ex)
            raise

        return _translate_hits(ms_response)

    def update_settings(self):
        """
        update index specific settings
        :return:
        """
        # Define filterable attributes

        return self._index.update_settings(INDEX_SETTINGS.get(self._prefixed_index_name, {}))
