"""
Tests for the Studio content search REST API.
"""
import functools
from django.test import override_settings
from rest_framework.test import APITestCase, APIClient
from unittest import mock

from organizations.models import Organization
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_cms

STUDIO_SEARCH_ENDPOINT_URL = "/api/content_search/v2/studio/"
MOCK_API_KEY_UID = "3203d764-370f-4e99-a917-d47ab7f29739"


def mock_meilisearch(enabled=True):
    """
    Decorator that mocks the required parts of content.search.views to simulate a running Meilisearch instance.
    """
    def decorator(func):
        """
        Overrides settings and patches to enable view tests.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with override_settings(
                MEILISEARCH_ENABLED=enabled,
                MEILISEARCH_PUBLIC_URL="http://meilisearch.url",
            ):
                with mock.patch(
                    'openedx.core.djangoapps.content.search.views._get_meili_api_key_uid',
                    return_value=MOCK_API_KEY_UID,
                ):
                    return func(*args, **kwargs)
        return wrapper
    return decorator


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

    @mock_meilisearch(enabled=False)
    def test_studio_search_unathenticated_disabled(self):
        """
        Whether or not Meilisearch is enabled, the API endpoint requires authentication.
        """
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 401

    @mock_meilisearch(enabled=True)
    def test_studio_search_unathenticated_enabled(self):
        """
        Whether or not Meilisearch is enabled, the API endpoint requires authentication.
        """
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 401

    @mock_meilisearch(enabled=False)
    def test_studio_search_disabled(self):
        """
        When Meilisearch is disabled, the Studio search endpoint gives a 404
        """
        self.client.login(username='student', password='student_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 404

    @mock_meilisearch(enabled=True)
    def test_studio_search_enabled(self):
        """
        We've implement fine-grained permissions on the meilisearch content,
        so any logged-in user can get a restricted API key for Meilisearch using the REST API.
        """
        self.client.login(username='student', password='student_pass')
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        assert result.data["index_name"] == "studio_content"
        assert result.data["url"] == "http://meilisearch.url"
        assert result.data["api_key"] and isinstance(result.data["api_key"], str)

    def _mock_generate_tenant_token(self, mock_search_client):
        """
        Return a mocked meilisearch.Client.generate_tenant_token method.
        """
        mock_generate_tenant_token = mock.Mock(return_value='restricted_api_key')
        mock_search_client.return_value = mock.Mock(
            generate_tenant_token=mock_generate_tenant_token,
        )
        return mock_generate_tenant_token

    @mock_meilisearch(enabled=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    def test_studio_search_student_no_access(self, mock_search_client):
        """
        Users without access to any courses or libraries will have all documents filtered out.
        """
        self.client.login(username='student', password='student_pass')
        mock_generate_tenant_token = self._mock_generate_tenant_token(mock_search_client)
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {
                    "filter": "org IN [] OR access_id IN []",
                }
            },
            expires_at=mock.ANY,
        )

    @mock_meilisearch(enabled=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    def test_studio_search_staff(self, mock_search_client):
        """
        Users with global staff access can search any document.
        """
        self.client.login(username='staff', password='staff_pass')
        mock_generate_tenant_token = self._mock_generate_tenant_token(mock_search_client)
        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {}
            },
            expires_at=mock.ANY,
        )

    @mock_meilisearch(enabled=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.get_access_ids_for_request')
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    def test_studio_search_limit_access_ids(self, mock_search_client, mock_get_access_ids):
        """
        Users with access to many courses or libraries will only be able to search content
        from the most recent 1_000 courses/libraries.
        """
        self.client.login(username='student', password='student_pass')
        mock_generate_tenant_token = self._mock_generate_tenant_token(mock_search_client)
        mock_get_access_ids.return_value = list(range(2000))
        expected_access_ids = list(range(1000))

        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_get_access_ids.assert_called_once()
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {
                    "filter": f"org IN [] OR access_id IN {expected_access_ids}",
                }
            },
            expires_at=mock.ANY,
        )

    @mock_meilisearch(enabled=True)
    @mock.patch('openedx.core.djangoapps.content.search.views.get_user_orgs')
    @mock.patch('openedx.core.djangoapps.content.search.views.meilisearch.Client')
    def test_studio_search_limit_orgs(self, mock_search_client, mock_get_user_orgs):
        """
        Users with access to many courses or libraries will only be able to search content
        from the most recent 1_000 courses/libraries.
        """
        self.client.login(username='student', password='student_pass')
        mock_generate_tenant_token = self._mock_generate_tenant_token(mock_search_client)
        mock_get_user_orgs.return_value = [
            Organization.objects.create(
                short_name=f"org{x}",
                description=f"Org {x}",
            ) for x in range(2000)
        ]
        expected_user_orgs = [
            f"org{x}" for x in range(1000)
        ]

        result = self.client.get(STUDIO_SEARCH_ENDPOINT_URL)
        assert result.status_code == 200
        mock_get_user_orgs.assert_called_once()
        mock_generate_tenant_token.assert_called_once_with(
            api_key_uid=MOCK_API_KEY_UID,
            search_rules={
                "studio_content": {
                    "filter": f"org IN {expected_user_orgs} OR access_id IN []",
                }
            },
            expires_at=mock.ANY,
        )
