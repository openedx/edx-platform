"""
Unit tests for the ImportBlocksView API endpoint.
"""

from unittest import mock

from django.urls import reverse
from organizations.models import Organization
from rest_framework.test import APIClient
from rest_framework import status

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.course_to_library_import import api
from cms.djangoapps.course_to_library_import.constants import COURSE_TO_LIBRARY_IMPORT_PURPOSE
from cms.djangoapps.course_to_library_import.data import CourseToLibraryImportStatus
from cms.djangoapps.course_to_library_import.models import CourseToLibraryImport
from openedx.core.djangoapps.content_libraries import api as content_libraries_api
from openedx.core.djangoapps.content_staging import api as content_staging_api
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory


class TestCourseToLibraryImportViewsMixin(SharedModuleStoreTestCase):
    """
    Mixin for tests that require a CourseToLibraryImport instance.
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

        self.ctli = api.create_import(
            user_id=self.admin_user.pk,
            library_key=str(self.library.key),
            course_ids=[str(self.course.id)],
        )


class ImportBlocksViewTest(TestCourseToLibraryImportViewsMixin):
    """
    Tests for ImportBlocksView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse('course_to_library_import:v0:import_blocks')

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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_data = self.valid_data.copy()
        invalid_data.pop('library_key')
        response = self.client.post(self.url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('cms.djangoapps.course_to_library_import.views.v0.views.api.import_library_from_staged_content')
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
            library_key=self.valid_data['library_key'],
            user_id=self.admin_user.pk,
            usage_ids=self.valid_data['usage_ids'],
            course_id=self.valid_data['course_id'],
            import_id=str(self.valid_data['import_id']),
            composition_level=self.valid_data['composition_level'],
            override=self.valid_data['override'],
        )


class TestCreateCourseToLibraryImportView(TestCourseToLibraryImportViewsMixin):
    """
    Tests for the CreateCourseToLibraryImportView API endpoint.
    """

    def setUp(self):
        super().setUp()

        self.url = reverse('course_to_library_import:v0:create_import', args=[self.library_id])
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

        response = self.client.post(self.url, self.valid_data, format='json')
        expected_response = {
            'course_ids': self.valid_data['course_ids'],
            'status': 'pending',
            'library_key': self.library_id,
            'uuid': str(CourseToLibraryImport.objects.last().uuid),
        }

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, expected_response)

    def test_non_existent_library(self):
        """
        Test that a non-existent library returns a 404 response.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            reverse('course_to_library_import:v0:create_import', args=['lib:org:lib2']),
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
        self.url = reverse('course_to_library_import:v0:get_import', args=[str(self.ctli.uuid)])

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
        course_structure = response.data[str(self.course.id)]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(list(response.data.keys()), self.ctli.course_ids.split())
        self.assertTrue(course_structure, expected_course_structure)

    def test_get_course_structure_not_found(self):
        """
        Test that the endpoint returns a 404 response when the import is not found.
        """
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(reverse(
            'course_to_library_import:v0:get_import',
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

        self.ctli.status = CourseToLibraryImportStatus.IMPORTED
        self.ctli.save()

        content_staging_api.get_ready_staged_content_by_user_and_purpose(
            self.admin_user.pk,
            COURSE_TO_LIBRARY_IMPORT_PURPOSE.format(course_id=str(self.course.id))
        ).delete()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {str(self.course.id): []})
