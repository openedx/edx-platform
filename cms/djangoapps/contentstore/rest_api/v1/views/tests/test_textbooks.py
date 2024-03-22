"""
Unit tests for the course's textbooks.
"""
from django.urls import reverse
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase

from ...mixins import PermissionAccessMixin


class CourseTextbooksViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseTextbooksView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:textbooks",
            kwargs={"course_id": self.course.id},
        )

    def test_success_response(self):
        """
        Check that endpoint is valid and success response.
        """
        expected_textbook = [
            {
                "tab_title": "Textbook Name",
                "chapters": [
                    {"title": "Chapter 1", "url": "/static/book.pdf"},
                    {"title": "Chapter 2", "url": "/static/story.pdf"},
                ],
                "id": "Textbook_Name",
            }
        ]
        self.course.pdf_textbooks = expected_textbook
        self.save_course()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["textbooks"], expected_textbook)
