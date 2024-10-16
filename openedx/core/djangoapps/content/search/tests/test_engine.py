"""
Test for the Meilisearch search engine.
"""

from datetime import datetime

import django.test
from django.utils import timezone
import pytest

from search.utils import DateRange, ValueRange
from openedx.core.djangoapps.content.search import engine


class DocumentEncoderTests(django.test.TestCase):
    """
    JSON encoder unit tests.
    """

    def test_document_encode_without_timezone(self):
        document = {
            "date": timezone.datetime(2024, 12, 31, 5, 0, 0),
        }
        encoder = engine.DocumentEncoder()
        encoded = encoder.encode(document)
        assert '{"date": "2024-12-31 05:00:00"}' == encoded

    def test_document_encode_with_timezone(self):
        document = {
            "date": timezone.datetime(
                2024, 12, 31, 5, 0, 0, tzinfo=timezone.get_fixed_timezone(0)
            ),
        }
        encoder = engine.DocumentEncoder()
        encoded = encoder.encode(document)
        assert '{"date": "2024-12-31 05:00:00+00:00"}' == encoded


class EngineTests(django.test.TestCase):
    """
    MeilisearchEngine tests.
    """

    def test_index_empty_document(self):
        assert {} == engine.process_nested_document({})

    def test_index_empty_document_raises_key_error(self):
        with pytest.raises(KeyError):
            engine.process_document({})

    def test_index(self):
        document = {
            "id": "abcd",
            "name": "My name",
            "title": "My title",
        }
        processed = engine.process_document(document)

        # Check that the source document was not modified
        self.assertNotIn(engine.PRIMARY_KEY_FIELD_NAME, document)

        # "id" field is preserved
        assert "abcd" == processed["id"]

        # Primary key field
        # can be verified with: echo -n "abcd" | sha1sum
        pk = "81fe8bfe87576c3ecb22426f8e57847382917acf"
        assert pk == processed[engine.PRIMARY_KEY_FIELD_NAME]

        # Additional fields
        assert "My name" == processed["name"]
        assert "My title" == processed["title"]

    def test_index_recursive(self):
        document = {"field": {"value": timezone.datetime(2024, 1, 1)}}
        processed = engine.process_nested_document(document)
        assert {
            "field": {
                "value": 1704067200.0,
                "value__utcoffset": None,
            }
        } == processed

    def test_index_datetime_no_tz(self):
        # No timezone
        document = {"id": "1", "dt": timezone.datetime(2024, 1, 1)}
        processed = engine.process_document(document)
        assert 1704067200.0 == processed["dt"]
        assert processed["dt__utcoffset"] is None
        # reverse serialisation
        reverse = engine.process_hit(processed)
        assert document == reverse

    def test_index_datetime_with_tz(self):
        # With timezone
        document = {
            "id": "1",
            "dt": timezone.datetime(
                2024,
                1,
                1,
                tzinfo=timezone.get_fixed_timezone(timezone.timedelta(seconds=3600)),
            ),
        }
        processed = engine.process_document(document)
        assert 1704063600.0 == processed["dt"]
        assert 3600 == processed["dt__utcoffset"]
        # reverse serialisation
        reverse = engine.process_hit(processed)
        assert document == reverse

    def test_search(self):
        meilisearch_results = {
            "hits": [
                {
                    "id": "id1",
                    engine.PRIMARY_KEY_FIELD_NAME: engine.id2pk("id1"),
                    "title": "title 1",
                    "_rankingScore": 0.8,
                },
                {
                    "id": "id2",
                    engine.PRIMARY_KEY_FIELD_NAME: engine.id2pk("id2"),
                    "title": "title 2",
                    "_rankingScore": 0.2,
                },
            ],
            "query": "demo",
            "processingTimeMs": 14,
            "limit": 20,
            "offset": 0,
            "estimatedTotalHits": 2,
        }
        processed_results = engine.process_results(meilisearch_results, "index_name")
        assert 14 == processed_results["took"]
        assert 2 == processed_results["total"]
        assert 0.8 == processed_results["max_score"]

        assert 2 == len(processed_results["results"])
        assert {
            "_id": "id1",
            "_index": "index_name",
            "_type": "_doc",
            "data": {
                "id": "id1",
                "title": "title 1",
            },
        } == processed_results["results"][0]

        assert {
            "_id": "id2",
            "_index": "index_name",
            "_type": "_doc",
            "data": {
                "id": "id2",
                "title": "title 2",
            },
        } == processed_results["results"][1]

    def test_search_with_facets(self):
        meilisearch_results = {
            "hits": [],
            "query": "",
            "processingTimeMs": 1,
            "limit": 20,
            "offset": 0,
            "estimatedTotalHits": 0,
            "facetDistribution": {
                "modes": {"audit": 1, "honor": 3},
                "facet2": {"val1": 1, "val2": 2, "val3": 3},
            },
        }
        processed_results = engine.process_results(meilisearch_results, "index_name")
        aggs = processed_results["aggs"]
        assert {
            "terms": {"audit": 1, "honor": 3},
            "total": 4.0,
            "other": 0,
        } == aggs["modes"]

    def test_search_params(self):
        params = engine.get_search_params()
        self.assertTrue(params["showRankingScore"])

        params = engine.get_search_params(from_=0)
        assert 0 == params["offset"]

    def test_search_params_exclude_dictionary(self):
        # Simple value
        params = engine.get_search_params(
            exclude_dictionary={"course_visibility": "none"}
        )
        assert ['NOT course_visibility = "none"'] == params["filter"]

        # Multiple IDs
        params = engine.get_search_params(exclude_dictionary={"id": ["1", "2"]})
        assert [
            f'NOT {engine.PRIMARY_KEY_FIELD_NAME} = "{engine.id2pk("1")}"',
            f'NOT {engine.PRIMARY_KEY_FIELD_NAME} = "{engine.id2pk("2")}"',
        ] == params["filter"]

    def test_search_params_field_dictionary(self):
        params = engine.get_search_params(
            field_dictionary={
                "course": "course-v1:testorg+test1+alpha",
                "org": "testorg",
            }
        )
        assert [
            'course = "course-v1:testorg+test1+alpha"',
            'org = "testorg"',
        ] == params["filter"]

    def test_search_params_filter_dictionary(self):
        params = engine.get_search_params(filter_dictionary={"key": "value"})
        assert ['key = "value" OR key NOT EXISTS'] == params["filter"]

    def test_search_params_value_range(self):
        params = engine.get_search_params(
            filter_dictionary={"value": ValueRange(lower=1, upper=2)}
        )
        assert ["(value >= 1 AND value <= 2) OR value NOT EXISTS"] == params["filter"]

        params = engine.get_search_params(
            filter_dictionary={"value": ValueRange(lower=1)}
        )
        assert ["value >= 1 OR value NOT EXISTS"] == params["filter"]

    def test_search_params_date_range(self):
        params = engine.get_search_params(
            filter_dictionary={
                "enrollment_end": DateRange(
                    lower=datetime(2024, 1, 1), upper=datetime(2024, 1, 2)
                )
            }
        )
        assert [
            "(enrollment_end >= 1704067200.0 AND enrollment_end <= 1704153600.0) OR enrollment_end NOT EXISTS"
        ] == params["filter"]

        params = engine.get_search_params(
            filter_dictionary={"enrollment_end": DateRange(lower=datetime(2024, 1, 1))}
        )
        assert [
            "enrollment_end >= 1704067200.0 OR enrollment_end NOT EXISTS"
        ] == params["filter"]
