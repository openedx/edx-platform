"""
Tests for the Studio content search REST API.
"""
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from unittest import mock

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase, skip_unless_cms

STUDIO_SEARCH_ENDPOINT_URL = "/api/content_search/v2/studio/"


@skip_unless_cms
class StudioSearchViewTest(CacheIsolationTestCase, APITestCase):
    """
    General tests for the Studio search REST API.
    """

    @classmethod
    def setUpTestData(cls):  # lint-amnesty, pylint: disable=super-method-not-called
        cls.staff = UserFactory.create(
            username='staff', email='staff@example.com', is_staff=True, password='staff_pass'
        )
        cls.student = UserFactory.create(
            username='student', email='student@example.com', is_staff=False, password='student_pass'
        )

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    @override_settings(MEILISEARCH_ENABLED=False)
    def test_studio_search_unathenticated_disabled(self):
        """
        Whether or not Meilisearch is enabled, the API endpoint requires authentication.
        """
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 401

    @override_settings(MEILISEARCH_ENABLED=True)
    def test_studio_search_unathenticated_enabled(self):
        """
        Whether or not Meilisearch is enabled, the API endpoint requires authentication.
        """
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 401

    @override_settings(MEILISEARCH_ENABLED=False)
    def test_studio_search_disabled(self):
        """
        When Meilisearch is disabled, the Studio search endpoint gives a 404
        """
        self.client.login(username='student', password='student_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 404

    @override_settings(MEILISEARCH_ENABLED=True)
    def test_studio_search_student_forbidden(self):
        """
        Until we implement fine-grained permissions, only global staff can use
        the Studio search endpoint.
        """
        self.client.login(username='student', password='student_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 403

    @override_settings(MEILISEARCH_ENABLED=True)
    @mock.patch('openedx.core.djangoapps.content.search.views._get_meili_api_key_uid')
    def test_studio_search_staff(self, mock_get_api_key_uid):
        """
        Global staff can get a restricted API key for Meilisearch using the REST
        API.
        """
        self.client.login(username='staff', password='staff_pass')
        mock_get_api_key_uid.return_value = "3203d764-370f-4e99-a917-d47ab7f29739"
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        assert result.data["index_name"] == "studio_content"
        assert result.data["url"].startswith("http")
        assert result.data["api_key"] and isinstance(result.data["api_key"], str)
