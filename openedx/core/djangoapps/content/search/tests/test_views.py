"""
Tests for the Studio content search REST API.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.test import override_settings
from rest_framework.test import APIClient, APITestCase

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_cms

from .. import api

STUDIO_SEARCH_ENDPOINT_URL = "/api/content_search/v2/studio/"


@skip_unless_cms
@patch("openedx.core.djangoapps.content.search.api._wait_for_meili_task", new=MagicMock(return_value=None))
@patch("openedx.core.djangoapps.content.search.api.MeilisearchClient")
class StudioSearchViewTest(APITestCase):
    """
    General tests for the Studio search REST API.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.staff = UserFactory.create(
            username='staff', email='staff@example.com', is_staff=True, password='staff_pass'
        )
        cls.student = UserFactory.create(
            username='student', email='student@example.com', is_staff=False, password='student_pass'
        )

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Clear the Meilisearch client to avoid side effects from other tests
        api.clear_meilisearch_client()

    @override_settings(MEILISEARCH_ENABLED=False)
    def test_studio_search_unathenticated_disabled(self, _meilisearch_client):
        """
        Whether or not Meilisearch is enabled, the API endpoint requires authentication.
        """
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 401

    @override_settings(MEILISEARCH_ENABLED=True)
    def test_studio_search_unathenticated_enabled(self, _meilisearch_client):
        """
        Whether or not Meilisearch is enabled, the API endpoint requires authentication.
        """
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 401

    @override_settings(MEILISEARCH_ENABLED=False)
    def test_studio_search_disabled(self, _meilisearch_client):
        """
        When Meilisearch is disabled, the Studio search endpoint gives a 404
        """
        self.client.login(username='student', password='student_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 404

    @override_settings(MEILISEARCH_ENABLED=True)
    def test_studio_search_student_forbidden(self, _meilisearch_client):
        """
        Until we implement fine-grained permissions, only global staff can use
        the Studio search endpoint.
        """
        self.client.login(username='student', password='student_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 403

    @override_settings(MEILISEARCH_ENABLED=True)
    def test_studio_search_staff(self, _meilisearch_client):
        """
        Global staff can get a restricted API key for Meilisearch using the REST
        API.
        """
        _meilisearch_client.return_value.generate_tenant_token.return_value = "api_key"
        self.client.login(username='staff', password='staff_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        assert result.data["index_name"] == "studio_content"
        assert result.data["url"].startswith("http")
        assert result.data["api_key"] and isinstance(result.data["api_key"], str)
