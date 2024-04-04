"""
Tests for the Studio content search REST API.
"""
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from unittest import mock

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_cms

STUDIO_SEARCH_ENDPOINT_URL = "/api/content_search/v2/studio/"
MOCK_API_KEY_UID = "3203d764-370f-4e99-a917-d47ab7f29739"


@skip_unless_cms
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

    @override_settings(MEILISEARCH_ENABLED=True, MEILISEARCH_PUBLIC_URL="http://meilisearch.url")
    @mock.patch('openedx.core.djangoapps.content.search.views._get_meili_api_key_uid')
    def test_studio_search_enabled(self, mock_get_api_key_uid):
        """
        We've implement fine-grained permissions on the meilisearch content,
        so any logged-in user can get a restricted API key for Meilisearch using the REST API.
        """
        self.client.login(username='student', password='student_pass')
        mock_get_api_key_uid.return_value = MOCK_API_KEY_UID
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        assert result.data["index_name"] == "studio_content"
        assert result.data["url"] == "http://meilisearch.url"
        assert result.data["api_key"] and isinstance(result.data["api_key"], str)

    @override_settings(MEILISEARCH_ENABLED=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    @mock.patch('openedx.core.djangoapps.content.search.views._get_meili_api_key_uid')
    def test_studio_search_student_no_access(self, mock_get_api_key_uid, mock_search_client):
        """
        Users without access to any courses or libraries will have all documents filtered out.
        """
        self.client.login(username='student', password='student_pass')
        mock_get_api_key_uid.return_value = MOCK_API_KEY_UID
        mock_generate_tenant_token = mock.Mock(return_value='restricted_api_key')
        mock_search_client.return_value = mock.Mock(
            generate_tenant_token=mock_generate_tenant_token,
        )
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {
                    "filter": "access_id IN []",
                }
            },
            expires_at=mock.ANY,
        )

    @override_settings(MEILISEARCH_ENABLED=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    @mock.patch('openedx.core.djangoapps.content.search.views._get_meili_api_key_uid')
    def test_studio_search_staff(self, mock_get_api_key_uid, mock_search_client):
        """
        Users with global staff access can search any document.
        """
        self.client.login(username='staff', password='staff_pass')
        mock_get_api_key_uid.return_value = MOCK_API_KEY_UID
        mock_generate_tenant_token = mock.Mock(return_value='restricted_api_key')
        mock_search_client.return_value = mock.Mock(
            generate_tenant_token=mock_generate_tenant_token,
        )
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {}
            },
            expires_at=mock.ANY,
        )

    @override_settings(MEILISEARCH_ENABLED=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.get_access_ids_for_request')
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    @mock.patch('openedx.core.djangoapps.content.search.views._get_meili_api_key_uid')
    def test_studio_search_limit(self, mock_get_api_key_uid, mock_search_client, mock_get_access_ids):
        """
        Users with access to many courses or libraries will only be able to search content
        from the most recent 1_000 courses/libraries.
        """
        self.client.login(username='student', password='student_pass')
        mock_get_api_key_uid.return_value = MOCK_API_KEY_UID
        mock_get_access_ids.return_value = list(range(2000))
        mock_generate_tenant_token = mock.Mock(return_value='restricted_api_key')
        mock_search_client.return_value = mock.Mock(
            generate_tenant_token=mock_generate_tenant_token,
        )
        expected_access_ids = list(range(1000))

        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_get_access_ids.assert_called_once()
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {
                    "filter": f"access_id IN {expected_access_ids}",
                }
            },
            expires_at=mock.ANY,
        )
