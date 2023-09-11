"""
Unit tests for course index outline.
"""
from django.urls import reverse
from django.test import RequestFactory
from rest_framework import status

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.rest_api.v1.mixins import PermissionAccessMixin
from cms.djangoapps.contentstore.views.course import _course_outline_json
from cms.djangoapps.contentstore.utils import get_lms_link_for_item


class CourseIndexViewTest(CourseTestCase, PermissionAccessMixin):
    """
    Tests for CourseIndexView.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.factory = RequestFactory()
        self.request = self.factory.get(f"/course/{self.course.id}")
        self.request.user = self.user
        self.url = reverse(
            "cms.djangoapps.contentstore:v1:course_index",
            kwargs={"course_id": self.course.id},
        )

    def test_course_index_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)
        expected_response = {
            "course_release_date": "Set Date",
            "course_structure": _course_outline_json(self.request, self.course),
            "deprecated_blocks_info": {
                "deprecated_enabled_block_types": [],
                "blocks": [],
                "advance_settings_url": f"/settings/advanced/{self.course.id}"
            },
            "discussions_incontext_feedback_url": "",
            "discussions_incontext_learnmore_url": "",
            "initial_state": None,
            "initial_user_clipboard": {
                "content": None,
                "source_usage_key": "",
                "source_context_title": "",
                "source_edit_url": ""
            },
            "language_code": "en",
            "lms_link": get_lms_link_for_item(self.course.location),
            "mfe_proctored_exam_settings_url": "",
            "notification_dismiss_url": None,
            "proctoring_errors": [],
            "reindex_link": f"/course/{self.course.id}/search_reindex",
            "rerun_notification_id": None
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)
