"""
Unit tests for home page view.
"""
import ddt
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.tests.test_libraries import LibraryTestCase


@ddt.ddt
class HomePageViewTest(CourseTestCase):
    """
    Tests for HomePageCoursesView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("cms.djangoapps.contentstore:v1:home")
        self.expected_response = {
            "allow_course_reruns": True,
            "allow_to_create_new_org": True,
            "allow_unicode_course_id": False,
            "allowed_organizations": [],
            "allowed_organizations_for_libraries": [],
            "archived_courses": [],
            "can_access_advanced_settings": True,
            "can_create_organizations": True,
            "course_creator_status": "granted",
            "courses": [],
            "in_process_course_actions": [],
            "libraries": [],
            "libraries_enabled": True,
            "libraries_v1_enabled": True,
            "libraries_v2_enabled": False,
            "taxonomies_enabled": True,
            "taxonomy_list_mfe_url": 'http://course-authoring-mfe/taxonomies',
            "request_course_creator_url": "/request_course_creator",
            "rerun_creator_status": True,
            "show_new_library_button": True,
            "show_new_library_v2_button": True,
            "split_studio_home": False,
            "studio_name": settings.STUDIO_NAME,
            "studio_short_name": settings.STUDIO_SHORT_NAME,
            "studio_request_email": "",
            "tech_support_email": "technical@example.com",
            "platform_name": settings.PLATFORM_NAME,
            "user_is_active": True,
        }

    def test_home_page_studio_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(self.expected_response, response.data)

    @override_settings(MEILISEARCH_ENABLED=True)
    def test_home_page_studio_with_meilisearch_enabled(self):
        """Check response content when Meilisearch is enabled"""
        response = self.client.get(self.url)

        expected_response = self.expected_response
        expected_response["libraries_v2_enabled"] = True

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    @override_settings(ORGANIZATIONS_AUTOCREATE=False)
    def test_home_page_studio_with_org_autocreate_disabled(self):
        """Check response content when Organization autocreate is disabled"""
        response = self.client.get(self.url)

        expected_response = self.expected_response
        expected_response["allow_to_create_new_org"] = False

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    def test_taxonomy_list_link(self):
        response = self.client.get(self.url)
        self.assertTrue(response.data['taxonomies_enabled'])
        self.assertEqual(
            response.data['taxonomy_list_mfe_url'],
            f'{settings.COURSE_AUTHORING_MICROFRONTEND_URL}/taxonomies'
        )


@ddt.ddt
class HomePageLibrariesViewTest(LibraryTestCase):
    """
    Tests for HomePageLibrariesView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("cms.djangoapps.contentstore:v1:libraries")

    def test_home_page_libraries_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)

        expected_response = {
            "libraries": [{
                'display_name': 'Test Library',
                'library_key': 'library-v1:org+lib',
                'url': '/library/library-v1:org+lib',
                'org': 'org',
                'number': 'lib',
                'can_edit': True
            }],
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(response.data)
        self.assertDictEqual(expected_response, response.data)
