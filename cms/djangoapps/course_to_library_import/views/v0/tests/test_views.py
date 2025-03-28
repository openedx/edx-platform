"""
Unit tests for the ImportBlocksView API endpoint.
"""

from unittest import mock

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from cms.djangoapps.course_to_library_import.data import CourseToLibraryImportStatus
from cms.djangoapps.course_to_library_import.tests.factories import CourseToLibraryImportFactory
from common.djangoapps.student.tests.factories import UserFactory


class ImportBlocksViewTest(TestCase):
    """
    Tests for ImportBlocksView.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.url = reverse('course_to_library_import:v0:import_blocks')

        self.admin_user = UserFactory(is_staff=True)
        self.non_admin_user = UserFactory()

        self.ctli = CourseToLibraryImportFactory(user_id=self.admin_user.pk, status=CourseToLibraryImportStatus.READY)

        self.valid_data = {
            'library_key': 'lib:org:lib1',
            'usage_ids': ['block-v1:org+course+run+type@problem+block@123'],
            'course_id': 'course-v1:org+course+run',
            'import_id': self.ctli.uuid,
            'composition_level': 'xblock',
            'override': False,
        }

    def test_permissions(self):
        """
        Test that only admin users can access the endpoint.
        """
        self.client.force_authenticate(user=self.non_admin_user)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(user=self.admin_user)
        with mock.patch('cms.djangoapps.course_to_library_import.views.v0.views.import_library_from_staged_content'):
            response = self.client.post(self.url, self.valid_data, format='json')
            self.assertEqual(response.status_code, 200)

    def test_invalid_data(self):
        """
        Test that invalid data returns appropriate errors.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, 400)

        invalid_data = self.valid_data.copy()
        invalid_data.pop('library_key')
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, 400)

    @mock.patch('cms.djangoapps.course_to_library_import.views.v0.views.import_library_from_staged_content')
    def test_successful_import(self, mock_import):
        """
        Test successful import returns a success response.
        """
        self.client.force_authenticate(user=self.admin_user)

        mock_import.return_value = None
        response = self.client.post(self.url, self.valid_data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'success'})

        mock_import.assert_called_once_with(
            library_key=self.valid_data['library_key'],
            user_id=self.admin_user.pk,
            usage_ids=self.valid_data['usage_ids'],
            course_id=self.valid_data['course_id'],
            import_id=self.valid_data['import_id'],
            composition_level=self.valid_data['composition_level'],
            override=self.valid_data['override'],
        )
