"""
Unit tests for the modulestore_migrator REST API v1 views.

These tests focus on validation, HTTP status codes, and serialization/deserialization.
Business logic is mocked out.
"""
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from cms.djangoapps.modulestore_migrator.rest_api.v1.views import MigrationViewSet

User = get_user_model()


class TestMigrationViewSetCreate(TestCase):
    """
    Test the MigrationViewSet.create() endpoint.

    Focus: validation, return codes, serialization/deserialization.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.factory = APIRequestFactory()
        self.view = MigrationViewSet.as_view({'post': 'create'})

        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password',
            is_staff=True,
            is_superuser=True
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='password'
        )

    @patch('cms.djangoapps.modulestore_migrator.rest_api.v1.views.start_migration_to_library')
    @patch('cms.djangoapps.modulestore_migrator.rest_api.v1.views.UserTaskStatus')
    def test_create_migration_success_with_minimal_data(self, mock_user_task_status, mock_start_migration):
        """
        Test successful migration creation with minimal required fields.

        Validates:
        - 201 status code is returned
        - Response contains expected serialized fields
        - Request data is properly deserialized
        """
        # Arrange: Mock the migration task and status
        mock_task = MagicMock()
        mock_task.id = 'test-task-id'
        mock_start_migration.return_value = mock_task

        mock_task_status = MagicMock()
        mock_task_status.uuid = uuid4()
        mock_task_status.state = 'Pending'
        mock_task_status.state_text = 'Pending'
        mock_task_status.completed_steps = 0
        mock_task_status.total_steps = 10
        mock_task_status.attempts = 1
        mock_task_status.created = '2025-01-01T00:00:00Z'
        mock_task_status.modified = '2025-01-01T00:00:00Z'
        mock_task_status.artifacts = []
        mock_task_status.migrations.all.return_value = []

        mock_user_task_status.objects.get.return_value = mock_task_status

        # Arrange: Prepare request with minimal required data
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'lib:TestOrg:TestLibrary',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert: Check response structure
        self.assertIn('uuid', response.data)
        self.assertIn('state', response.data)
        self.assertIn('state_text', response.data)
        self.assertIn('completed_steps', response.data)
        self.assertIn('total_steps', response.data)
        self.assertIn('parameters', response.data)

        # Assert: Check that start_migration_to_library was called with deserialized data
        mock_start_migration.assert_called_once()
        call_kwargs = mock_start_migration.call_args[1]
        self.assertEqual(call_kwargs['user'], self.admin_user)
        self.assertEqual(str(call_kwargs['source_key']), 'course-v1:TestOrg+TestCourse+TestRun')
        self.assertEqual(str(call_kwargs['target_library_key']), 'lib:TestOrg:TestLibrary')

    def test_create_migration_invalid_source_key(self):
        """
        Test that invalid source key returns 400 Bad Request.

        Validates:
        - 400 status code is returned
        - Error message mentions validation failure
        """
        # Arrange: Prepare request with invalid source key
        request_data = {
            'source': 'not-a-valid-key',
            'target': 'lib:TestOrg:TestLibrary',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('source', response.data)

    def test_create_migration_invalid_target_key(self):
        """
        Test that invalid target library key returns 400 Bad Request.

        Validates:
        - 400 status code is returned
        - Error message mentions target validation failure
        """
        # Arrange: Prepare request with invalid target key
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'not-a-valid-library-key',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('target', response.data)

    def test_create_migration_missing_required_fields(self):
        """
        Test that missing required fields returns 400 Bad Request.

        Validates:
        - 400 status code is returned when source is missing
        - 400 status code is returned when target is missing
        """
        # Test missing source
        request_data = {
            'target': 'lib:TestOrg:TestLibrary',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('source', response.data)

        # Test missing target
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)
        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('target', response.data)

    def test_create_migration_unauthenticated_user(self):
        """
        Test that unauthenticated requests return 401 Unauthorized.

        Validates:
        - 401 status code for unauthenticated requests
        """
        # Arrange: Prepare request without authentication
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'lib:TestOrg:TestLibrary',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        # Note: No force_authenticate call

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_create_migration_non_admin_user(self):
        """
        Test that non-admin users cannot create migrations.

        Validates:
        - 403 Forbidden status code for non-admin users
        """
        # Arrange: Prepare request with non-admin user
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'lib:TestOrg:TestLibrary',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.regular_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('cms.djangoapps.modulestore_migrator.rest_api.v1.views.start_migration_to_library')
    @patch('cms.djangoapps.modulestore_migrator.rest_api.v1.views.UserTaskStatus')
    def test_create_migration_with_optional_fields(self, mock_user_task_status, mock_start_migration):
        """
        Test migration creation with all optional fields provided.

        Validates:
        - Optional fields are properly deserialized
        - Default values are not used when explicit values provided
        """
        # Arrange: Mock the migration task and status
        mock_task = MagicMock()
        mock_task.id = 'test-task-id'
        mock_start_migration.return_value = mock_task

        mock_task_status = MagicMock()
        mock_task_status.uuid = uuid4()
        mock_task_status.state = 'Pending'
        mock_task_status.state_text = 'Pending'
        mock_task_status.completed_steps = 0
        mock_task_status.total_steps = 10
        mock_task_status.attempts = 1
        mock_task_status.created = '2025-01-01T00:00:00Z'
        mock_task_status.modified = '2025-01-01T00:00:00Z'
        mock_task_status.artifacts = []
        mock_task_status.migrations.all.return_value = []

        mock_user_task_status.objects.get.return_value = mock_task_status

        # Arrange: Prepare request with all optional fields
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'lib:TestOrg:TestLibrary',
            'target_collection_slug': 'my-collection',
            'composition_level': 'unit',
            'repeat_handling_strategy': 'update',
            'preserve_url_slugs': False,
            'forward_source_to_target': True,
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert: Check that all optional fields were passed correctly
        mock_start_migration.assert_called_once()
        call_kwargs = mock_start_migration.call_args[1]
        self.assertEqual(call_kwargs['target_collection_slug'], 'my-collection')
        self.assertEqual(call_kwargs['composition_level'], 'unit')
        self.assertEqual(call_kwargs['repeat_handling_strategy'], 'update')
        self.assertEqual(call_kwargs['preserve_url_slugs'], False)
        self.assertEqual(call_kwargs['forward_source_to_target'], True)

    def test_create_migration_invalid_composition_level(self):
        """
        Test that invalid composition_level returns 400 Bad Request.

        Validates:
        - 400 status code for invalid enum value
        """
        # Arrange: Prepare request with invalid composition_level
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'lib:TestOrg:TestLibrary',
            'composition_level': 'invalid_level',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('composition_level', response.data)

    def test_create_migration_invalid_repeat_handling_strategy(self):
        """
        Test that invalid repeat_handling_strategy returns 400 Bad Request.

        Validates:
        - 400 status code for invalid enum value
        """
        # Arrange: Prepare request with invalid repeat_handling_strategy
        request_data = {
            'source': 'course-v1:TestOrg+TestCourse+TestRun',
            'target': 'lib:TestOrg:TestLibrary',
            'repeat_handling_strategy': 'invalid_strategy',
        }
        request = self.factory.post(
            '/api/modulestore_migrator/v1/migrations/',
            data=request_data,
            format='json'
        )
        force_authenticate(request, user=self.admin_user)

        # Act: Make the request
        response = self.view(request)

        # Assert: Check status code and error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeat_handling_strategy', response.data)
