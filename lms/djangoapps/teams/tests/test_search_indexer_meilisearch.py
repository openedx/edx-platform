"""
Tests for Meilisearch-specific behavior in CourseTeamIndexer and TeamsListView.

These tests avoid any real network calls by patching meilisearch helpers.
"""

from unittest.mock import patch, MagicMock

import ddt
from django.test import override_settings
from django.urls import reverse

from rest_framework.test import APIClient

from lms.djangoapps.teams.models import CourseTeam
from lms.djangoapps.teams.search_indexes import CourseTeamIndexer
from lms.djangoapps.teams.tests.test_views import TeamAPITestCase


@ddt.ddt
class TestMeilisearchFilterables(TeamAPITestCase):
    """Validate that we attempt to configure Meilisearch filterable attributes."""

    @override_settings(SEARCH_ENGINE="search.meilisearch.MeilisearchEngine")
    @patch("search.meilisearch.get_or_create_meilisearch_index")
    @patch("search.meilisearch.get_meilisearch_index_name")
    @patch("search.meilisearch.get_meilisearch_client")
    @patch("search.meilisearch.update_index_filterables")
    def test_engine_configures_filterables(
        self,
        mock_update_filterables,
        mock_get_client,
        mock_get_index_name,
        mock_get_or_create,
    ):
        # Arrange minimal meilisearch plumbing
        mock_get_client.return_value = MagicMock()
        mock_get_index_name.return_value = "prefixed-course_team_index"
        mock_get_or_create.return_value = MagicMock()

        # Exercise engine access (should attempt to ensure filterables)
        engine = CourseTeamIndexer.engine()
        assert engine is not None

        # Assert that filterables were attempted to be ensured
        mock_update_filterables.assert_called()
        args, kwargs = mock_update_filterables.call_args
        # args = (client, index, filterables)
        assert isinstance(args[0], MagicMock)
        assert isinstance(args[1], MagicMock)
        assert set(args[2]) == set(CourseTeamIndexer.MEILISEARCH_FILTERABLES)


class _FailingSearchEngine:
    """A tiny stub search engine that raises during search."""

    def __init__(self, *_, **__):
        pass

    def search(self, *_, **__):  # pylint: disable=unused-argument
        raise RuntimeError("search backend failed")

    def index(self, *_args, **_kwargs):
        pass

    def remove(self, *_args, **_kwargs):
        pass


class TestSearchFailureJsonResponse(TeamAPITestCase):
    """Ensure the API returns JSON 503 on search backend failures."""

    def test_search_failure_returns_json_503(self):
        client = APIClient()
        # Log in as staff so we can query
        client.login(username=self.users['staff'].username, password='test')

        with override_settings(SEARCH_ENGINE="search.tests.mock_search_engine.MockSearchEngine"):
            # Patch SearchEngine.get_search_engine to return our failing stub
            with patch("search.search_engine_base.SearchEngine.get_search_engine", return_value=_FailingSearchEngine()):
                url = reverse('teams_list')
                response = client.get(
                    url,
                    data={
                        'course_id': str(self.test_course_1.id),
                        'text_search': 'anything',
                    },
                )
                assert response.status_code == 503
                data = response.json()
                # Minimal structure check: we expect a dict with a developer message
                assert isinstance(data, dict)
                assert 'developer_message' in data or 'field_errors' in data

