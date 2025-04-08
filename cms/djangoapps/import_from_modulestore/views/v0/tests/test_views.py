"""
Unit tests for the ImportBlocksView API endpoint.
"""

from unittest import mock

from django.urls import reverse
from organizations.models import Organization
from opaque_keys.edx.keys import CourseKey
from rest_framework.test import APIClient
from rest_framework import status

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.import_from_modulestore import api
from cms.djangoapps.import_from_modulestore.models import Import
from openedx.core.djangoapps.content_libraries import api as content_libraries_api
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory


class TestCourseToLibraryImportViewsMixin(SharedModuleStoreTestCase):
    """
    Mixin for tests that require a Import instance.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()

        self.library = content_libraries_api.create_library(
            org=Organization.objects.create(name='Organization 1', short_name='org1'),
            slug='lib_1',
            title='Library Org 1',
            description='This is a library from Org 1',
        )
        self.library_id = str(self.library.key)

        self.admin_user = UserFactory(is_staff=True)
        self.non_admin_user = UserFactory()

        self.course = CourseFactory.create()
        self.chapter = BlockFactory.create(category='chapter', parent=self.course)
        self.sequential = BlockFactory.create(category='sequential', parent=self.chapter)
        self.vertical = BlockFactory.create(category='vertical', parent=self.sequential)
        self.problem = BlockFactory.create(category='problem', parent=self.vertical)

        with self.captureOnCommitCallbacks(execute=True):
            self.import_event = api.create_import(
                user_id=self.admin_user.pk,
                learning_package_id=self.library.learning_package.id,
                source_key=self.course.id,
            )


class ImportBlocksViewTest(TestCourseToLibraryImportViewsMixin):
    """
    Tests for ImportBlocksView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('import_from_modulestore:v0:import_blocks')

        self.valid_data = {
            'usage_ids': ['block-v1:org+course+run+type@problem+block@123'],
            'import_uuid': self.import_event.uuid,
            'composition_level': 'xblock',
            'override': False,
        }

    def test_permissions(self):
        """
        Test that only admin users can access the endpoint.
        """
        self.client.force_authenticate(user=self.non_admin_user)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_data(self):
        """
        Test that invalid data returns appropriate errors.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        invalid_data = self.valid_data.copy()
        invalid_data['usage_ids'] = '12345'
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('cms.djangoapps.import_from_modulestore.views.v0.views.api.import_course_staged_content_to_library')
    def test_successful_import(self, mock_import):
        """
        Test successful import returns a success response.
        """
        self.client.force_authenticate(user=self.admin_user)

        mock_import.return_value = None
        response = self.client.post(self.url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'success'})

        mock_import.assert_called_once_with(
            usage_ids=self.valid_data['usage_ids'],
            import_uuid=str(self.valid_data['import_uuid']),
            user_id=self.admin_user.pk,
            composition_level=self.valid_data['composition_level'],
            override=self.valid_data['override'],
        )


class TestCreateCourseToLibraryImportView(TestCourseToLibraryImportViewsMixin):
    """
    Tests for the CreateImportView API endpoint.
    """

    def setUp(self):
        super().setUp()

        self.url = reverse('import_from_modulestore:v0:create_import', args=[self.library_id])
        self.valid_data = {
            'course_ids': ['course-v1:org+course+run', 'course-v1:org2+course2+run2'],
        }

    def test_permissions(self):
        """
        Test that only admin users can access the endpoint.
        """
        self.client.force_authenticate(user=self.non_admin_user)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_data(self):
        """
        Test that invalid data returns appropriate errors.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            self.url,
            {'course_ids': 'course-v1:org+course+run course-v1:org2+course2+run2'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_import(self):
        """
        Test successful import returns a success response.
        """
        self.client.force_authenticate(user=self.admin_user)
        expected_response = {
            'result': []
        }

        response = self.client.post(self.url, self.valid_data, format='json')

        for course_id in self.valid_data['course_ids']:
            expected_response['result'].append({
                'uuid': str(Import.objects.get(source_key=CourseKey.from_string(course_id)).uuid),
                'course_id': course_id,
                'status': 'Pending',
                'library_key': str(self.library_id),
            })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, expected_response)

    def test_non_existent_library(self):
        """
        Test that a non-existent library returns a 404 response.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            reverse('import_from_modulestore:v0:create_import', args=['lib:org:lib2']),
            self.valid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetCourseStructureToLibraryImportView(TestCourseToLibraryImportViewsMixin):
    """
    Tests for the GetCourseStructureToLibraryImportView API endpoint.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('import_from_modulestore:v0:get_import', args=[str(self.import_event.uuid)])

    def test_get_course_structure(self):
        """
        Test that the endpoint returns the correct course structure.
        """
        expected_course_structure = [{
            str(self.chapter.location): self.chapter.display_name,
            'children': [{
                str(self.sequential.location): self.sequential.display_name,
                'children': [{
                    str(self.vertical.location): self.vertical.display_name,
                    'children': [{
                        str(self.problem.location): self.problem.display_name,
                    }]
                }]
            }]
        }]

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data, expected_course_structure)

    def test_get_course_structure_not_found(self):
        """
        Test that the endpoint returns a 404 response when the import is not found.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(reverse(
            'import_from_modulestore:v0:get_import',
            kwargs={'course_to_lib_uuid': '593e93d7-ed64-4147-bb5c-4cfcb1cf80b1'})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_course_structure_no_permissions(self):
        """
        Test that the endpoint returns a 403 response when the user does not have permissions.
        """
        self.client.force_authenticate(user=self.non_admin_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_course_structure_for_imported_course(self):
        """
        Test that the endpoint returns an empty course structure for an imported course.
        """
        self.client.force_authenticate(user=self.admin_user)
        self.import_event.imported()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
