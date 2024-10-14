"""
This is a search engine for Meilisearch. It implements the edx-search's SearchEngine
API, such that it can be setup as a drop-in replacement for the ElasticSearchEngine. To
switch to this engine, you should run a Meilisearch instance and define the following
setting:

    SEARCH_ENGINE = "openedx.core.djangoapps.content.search.engine.MeilisearchEngine"

You will then need to create the new indices by running:

    ./manage.py lms shell -c "from openedx.core.djangoapps.content.search import engine; engine.create_indexes()"

For more information about the Meilisearch API in Python, check
https://github.com/meilisearch/meilisearch-python

When implementing a new index, you might discover that you need to list explicit filterable
fields. Typically, you try to index new documents, and Meilisearch fails with the
following response:

    meilisearch.errors.MeilisearchApiError: MeilisearchApiError. Error code: invalid_search_filter.
    Error message: Attribute `field3` is not filterable. Available filterable attributes are:
    `field1 field2 _pk`.

In such cases, the filterable field should be added to INDEX_FILTERABLES below. And you should
then run the `create_indexes()` function again, as indicated above.

This search engine was tested for the following indexes:

1. course_info ("course discovery"):
    - Enable the course discovery feature: FEATURES["ENABLE_COURSE_DISCOVERY"] = True
    - A search bar appears in the LMS landing page.
    - Content is automatically indexed every time a course is edited in the studio.
2. courseware_content ("courseware search"):
    - Enable the courseware search waffle flag:

        ./manage.py lms waffle_flag --create --everyone courseware.mfe_courseware_search

    - Enable the following feature flags:

        FEATURES["ENABLE_COURSEWARE_INDEX"] = True
        FEATURES["ENABLE_COURSEWARE_SEARCH"] = True
    - Reindex courseware content by running: ./manage.py cms reindex_course --active
    - Alternatively, reindex course content by clicking the "Reindex" button in the Studio.
    - In the learning MFE, a course search bar appears when opening a course.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import logging
import typing as t

import meilisearch

from django.conf import settings
from django.utils import timezone

from search.search_engine_base import SearchEngine
from search.utils import ValueRange


logger = logging.getLogger(__name__)

PRIMARY_KEY_FIELD_NAME = "_pk"
UTC_OFFSET_SUFFIX = "__utcoffset"


# In Meilisearch, we need to explicitly list fields for which we expect to define
# filters and aggregation functions.
# This is different than Elasticsearch where we can aggregate results over any field.
# Here, we list facet fields per index.
# Reference: https://www.meilisearch.com/docs/learn/filtering_and_sorting/search_with_facet_filters
# Note that index names are hard-coded here, because they are hardcoded anyway across all of edx-search.
INDEX_FILTERABLES = {
    "course_info": [
        "language",  # aggregate by language, mode, org
        "modes",
        "org",
        "catalog_visibility",  # exclude visibility="none"
        "enrollment_end",  # include only enrollable courses
    ],
    "courseware_content": [
        PRIMARY_KEY_FIELD_NAME,  # exclude some specific documents based on ID
        "course",  # search courseware content by course
        "org",  # used during indexing
        "start_date",  # limit search to started courses
    ],
}


class MeilisearchEngine(SearchEngine):
    """
    Meilisearch-compatible search engine. We work very hard to produce an output that is
    compliant with edx-search's ElasticSearchEngine.
    """

    def __init__(self, index=None):
        super().__init__(index=index)
        self.meilisearch_index = get_meilisearch_index(self.index_name)

    @property
    def meilisearch_index_name(self):
        """
        The index UID is its name.
        """
        return self.meilisearch_index.uid

    def index(self, sources: list[dict[str, t.Any]], **kwargs):
        """
        Index a number of documents, which can have just any type.
        """
        logger.debug(
            "Index request: index=%s sources=%s kwargs=%s",
            self.meilisearch_index_name,
            sources,
            kwargs,
        )
        self.meilisearch_index.add_documents(
            [process_document(source) for source in sources],
            serializer=DocumentEncoder,
        )

    def search(
        self,
        query_string=None,
        field_dictionary=None,
        filter_dictionary=None,
        exclude_dictionary=None,
        aggregation_terms=None,
        # exclude_ids=None, # deprecated
        # use_field_match=False, # deprecated
        log_search_params=False,
        **kwargs,
    ):
        """
        See meilisearch docs: https://www.meilisearch.com/docs/reference/api/search
        """

        opt_params = get_search_params(
            field_dictionary=field_dictionary,
            filter_dictionary=filter_dictionary,
            exclude_dictionary=exclude_dictionary,
            aggregation_terms=aggregation_terms,
            **kwargs,
        )
        if log_search_params:
            logger.info(opt_params)

        meilisearch_results = self.meilisearch_index.search(query_string, opt_params)
        return process_results(meilisearch_results, self.index_name)

    def remove(self, doc_ids, **kwargs):
        logger.debug(
            "Remove request: index=%s, doc_ids=%s kwargs=%s",
            self.meilisearch_index_name,
            doc_ids,
            kwargs,
        )
        if doc_ids:
            self.meilisearch_index.delete_documents(
                [id2pk(doc_id) for doc_id in doc_ids]
            )


class DocumentEncoder(json.JSONEncoder):
    """
    Custom encoder, useful in particular to encode datetime fields.
    Ref: https://github.com/meilisearch/meilisearch-python?tab=readme-ov-file#custom-serializer-for-documents-
    """

    def default(self, o):
        if isinstance(o, datetime):
            return str(o)
        return super().default(o)


def create_indexes():
    """
    This is an initialization function that creates indexes and makes sure that they
    support the right facetting.
    """
    client = get_meilisearch_client()
    for index_name, filterables in INDEX_FILTERABLES.items():
        meilisearch_index_name = get_meilisearch_index_name(index_name)
        try:
            index = client.get_index(meilisearch_index_name)
        except meilisearch.errors.MeilisearchApiError as e:
            if e.code != "index_not_found":
                raise
            client.create_index(
                meilisearch_index_name, {"primaryKey": PRIMARY_KEY_FIELD_NAME}
            )
            # Get the index again
            index = client.get_index(meilisearch_index_name)

        # Update filterables
        if filterables and index.get_filterable_attributes() != filterables:
            index.update_filterable_attributes(filterables)


def get_meilisearch_index(index_name: str):
    """
    Return a meilisearch index.

    Note that the index may not exist, and it will be created on first insertion.
    ideally, the initialisation function `create_indexes` should be run first.
    """
    meilisearch_client = get_meilisearch_client()
    meilisearch_index_name = get_meilisearch_index_name(index_name)
    return meilisearch_client.index(meilisearch_index_name)


def get_meilisearch_client():
    return meilisearch.Client(
        settings.MEILISEARCH_URL, api_key=settings.MEILISEARCH_API_KEY
    )


def get_meilisearch_index_name(index_name: str) -> str:
    """
    Return the index name in Meilisearch associated to a hard-coded index name.

    This is useful for multi-tenant Meilisearch: just define a different prefix for
    every tenant.

    Usually, meilisearch API keys are allowed to access only certain index prefixes.
    Make sure that your API key matches the prefix.
    """
    return settings.MEILISEARCH_INDEX_PREFIX + index_name


def process_document(doc: dict[str, t.Any]) -> dict[str, t.Any]:
    """
    Process document before indexing.

    We make a copy to avoid modifying the source document.
    """
    processed = {PRIMARY_KEY_FIELD_NAME: id2pk(doc["id"])}
    for key, value in doc.items():
        if isinstance(value, timezone.datetime):
            # Convert datetime objects to timestamp, and store the timezone in a
            # separate field with a suffix given by UTC_OFFSET_SUFFIX.
            utcoffset = None
            if value.tzinfo:
                utcoffset = value.utcoffset().seconds
            processed[key] = value.timestamp()
            processed[f"{key}{UTC_OFFSET_SUFFIX}"] = utcoffset
        elif isinstance(value, dict):
            processed[key] = process_document(value)
        else:
            # Pray that there are not datetime objects inside lists
            processed[key] = value
    return processed


def id2pk(value: str) -> str:
    """
    Convert a document "id" field into a primary key that is compatible with Meilisearch.

    This step is necessary because the "id" is typically a course id, which includes
    colon ":" characters, which are not supported by Meilisearch. Source:
    https://www.meilisearch.com/docs/learn/getting_started/primary_key#formatting-the-document-id
    """
    return hashlib.sha1(value.encode()).hexdigest()


def get_search_params(
    field_dictionary=None,
    filter_dictionary=None,
    exclude_dictionary=None,
    aggregation_terms=None,
    **kwargs,
) -> dict[str, t.Any]:
    """
    Return a dictionary of parameters that should be passed to the Meilisearch client
    `.search()` method.
    """
    params = {"showRankingScore": True}

    # Aggregation
    if aggregation_terms:
        params["facets"] = list(aggregation_terms.keys())

    # Exclusion and inclusion filters
    filters = []
    if field_dictionary:
        filters += get_filter_rules(field_dictionary)
    if filter_dictionary:
        filters += get_filter_rules(filter_dictionary, optional=True)
    if exclude_dictionary:
        filters += get_filter_rules(exclude_dictionary, exclude=True)
    if filters:
        params["filter"] = filters

    # Offset/Size
    if "from_" in kwargs:
        params["offset"] = kwargs["from_"]
    if "size" in kwargs:
        params["limit"] = kwargs["size"]

    return params


def get_filter_rules(
    rule_dict: dict[str, t.Any], exclude: bool = False, optional: bool = False
) -> list[str]:
    """
    Convert inclusion/exclusion rules.
    """
    rules = []
    for key, value in rule_dict.items():
        if isinstance(value, list):
            for v in value:
                rules.append(
                    get_filter_rule(key, v, exclude=exclude, optional=optional)
                )
        else:
            rules.append(
                get_filter_rule(key, value, exclude=exclude, optional=optional)
            )
    return rules


def get_filter_rule(
    key: str, value: str, exclude: bool = False, optional: bool = False
) -> str:
    """
    Meilisearch filter rule.

    See: https://www.meilisearch.com/docs/learn/filtering_and_sorting/filter_expression_reference
    """
    prefix = "NOT " if exclude else ""
    if key == "id":
        key = PRIMARY_KEY_FIELD_NAME
        value = id2pk(value)
    if isinstance(value, str):
        rule = f'{prefix}{key} = "{value}"'
    elif isinstance(value, ValueRange):
        constraints = []
        lower = value.lower
        if isinstance(lower, timezone.datetime):
            lower = lower.timestamp()
        upper = value.upper
        if isinstance(upper, timezone.datetime):
            upper = upper.timestamp()
        # I know that the following fails if value == 0, but we are being
        # consistent with the behaviour in the elasticsearch engine.
        if lower:
            constraints.append(f"{key} >= {lower}")
        if upper:
            constraints.append(f"{key} <= {upper}")
        rule = " AND ".join(constraints)
        if len(constraints) > 1:
            rule = f"({rule})"
    else:
        raise ValueError(f"Unknown value type: {value.__class__}")
    if optional:
        rule += f" OR {key} NOT EXISTS"
    return rule


def process_results(results: dict[str, t.Any], index_name: str) -> dict[str, t.Any]:
    """
    Convert results produced by Meilisearch into results that are compatible with the
    edx-search engine API.

    Example input:

        {
            'hits': [
                {
                    'pk': 'f381d4f1914235c9532576c0861d09b484ade634',
                    'id': 'course-v1:OpenedX+DemoX+DemoCourse',
                    ...
                    "_rankingScore": 0.865,
                },
                ...
            ],
            'query': 'demo',
            'processingTimeMs': 0,
            'limit': 20,
            'offset': 0,
            'estimatedTotalHits': 1
        }

    Example output:

        {
                'took': 13,
                'total': 1,
                'max_score': 0.4001565,
                'results': [
                    {
                        '_index': 'course_info',
                        '_type': '_doc',
                        '_id': 'course-v1:OpenedX+DemoX+DemoCourse',
                        '_ignored': ['content.overview.keyword'], # removed
                        'data': {
                            'id': 'course-v1:OpenedX+DemoX+DemoCourse',
                            'course': 'course-v1:OpenedX+DemoX+DemoCourse',
                            'content': {
                                'display_name': 'Open edX Demo Course',
                                ...
                            },
                            'image_url': '/asset-v1:OpenedX+DemoX+DemoCourse+type@asset+block@thumbnail_demox.jpeg',
                            'start': '2020-01-01T00:00:00+00:00',
                            ...
                        },
                        'score': 0.4001565
                    }
                ],
                'aggs': {
                    'modes': {
                        'terms': {'audit': 1},
                        'total': 1.0,
                        'other': 0
                    },
                    'org': {
                        'terms': {'OpenedX': 1}, 'total': 1.0, 'other': 0
                    },
                    'language': {'terms': {'en': 1}, 'total': 1.0, 'other': 0}
                }
            }
    """
    # Base
    processed = {
        "took": results["processingTimeMs"],
        "total": results["estimatedTotalHits"],
        "results": [],
        "aggs": {},
    }

    # Hits
    max_score = 0
    for result in results["hits"]:
        result = process_hit(result)
        score = result.pop("_rankingScore")
        max_score = max(max_score, score)
        processed_result = {
            "_id": result["id"],
            "_index": index_name,
            "_type": "_doc",
            "data": result,
        }
        processed["results"].append(processed_result)
    processed["max_score"] = max_score

    # Aggregates/Facets
    for facet_name, facet_distribution in results.get("facetDistribution", {}).items():
        total = sum(facet_distribution.values())
        processed["aggs"][facet_name] = {
            "terms": facet_distribution,
            "total": total,
            "other": 0,
        }
    return processed


def process_hit(hit: dict[str, t.Any]) -> dict[str, t.Any]:
    """
    Convert a search result back to the ES format.
    """
    processed = deepcopy(hit)

    # Remove primary key field
    try:
        processed.pop(PRIMARY_KEY_FIELD_NAME)
    except KeyError:
        pass

    # Convert datetime fields back to datetime
    for key, value in hit.items():
        if key.endswith(UTC_OFFSET_SUFFIX):
            utcoffset = processed.pop(key)
            key = key[: -len(UTC_OFFSET_SUFFIX)]
            timestamp = hit[key]
            tz = (
                timezone.get_fixed_timezone(timezone.timedelta(seconds=utcoffset))
                if utcoffset
                else None
            )
            processed[key] = timezone.datetime.fromtimestamp(timestamp, tz=tz)
    return processed
