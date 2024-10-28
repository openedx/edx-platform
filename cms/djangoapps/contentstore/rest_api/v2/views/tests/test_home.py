"""
Unit tests for home page view.
"""
from collections import OrderedDict
from datetime import datetime, timedelta
from unittest.mock import patch

import ddt
import pytz
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_switch
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.utils import reverse_course_url
from cms.djangoapps.contentstore.views.course import ENABLE_GLOBAL_STAFF_OPTIMIZATION
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

FEATURES_WITH_HOME_PAGE_COURSE_V2_API = settings.FEATURES.copy()
FEATURES_WITH_HOME_PAGE_COURSE_V2_API['ENABLE_HOME_PAGE_COURSE_API_V2'] = True


@override_settings(FEATURES=FEATURES_WITH_HOME_PAGE_COURSE_V2_API)
@ddt.ddt
class HomePageCoursesViewV2Test(CourseTestCase):
    """
    Tests for HomePageView view version 2.
    """

    def setUp(self):
        super().setUp()
        self.api_v2_url = reverse("cms.djangoapps.contentstore:v2:courses")
        self.api_v1_url = reverse("cms.djangoapps.contentstore:v1:courses")
        self.active_course = CourseOverviewFactory.create(
            id=self.course.id,
            org=self.course.org,
            display_name=self.course.display_name,
        )
        archived_course_key = self.store.make_course_key('demo-org', 'demo-number', 'demo-run')
        self.archived_course = CourseOverviewFactory.create(
            display_name="Demo Course (Sample)",
            id=archived_course_key,
            org=archived_course_key.org,
            end=(datetime.now() - timedelta(days=365)).replace(tzinfo=pytz.UTC),
        )

    def test_home_page_response(self):
        """Get list of courses available to the logged in user.

        Expected result:
        - A paginated response.
        - A list of courses available to the logged in user.
        """
        response = self.client.get(self.api_v2_url)
        course_id = str(self.course.id)
        archived_course_id = str(self.archived_course.id)

        expected_data = {
            "courses": [
                OrderedDict([
                    ("course_key", course_id),
                    ("display_name", self.course.display_name),
                    ("lms_link", f'//{settings.LMS_BASE}/courses/{course_id}/jump_to/{self.course.location}'),
                    ("cms_link", f'//{settings.CMS_BASE}{reverse_course_url("course_handler", self.course.id)}'),
                    ("number", self.course.number),
                    ("org", self.course.org),
                    ("rerun_link", f'/course_rerun/{course_id}'),
                    ("run", self.course.id.run),
                    ("url", f'/course/{course_id}'),
                    ("is_active", True),
                ]),
                OrderedDict([
                    ("course_key", str(self.archived_course.id)),
                    ("display_name", self.archived_course.display_name),
                    (
                        "lms_link",
                        f'//{settings.LMS_BASE}/courses/{archived_course_id}/jump_to/{self.archived_course.location}'
                    ),
                    (
                        "cms_link",
                        f'//{settings.CMS_BASE}{reverse_course_url("course_handler", self.archived_course.id)}',
                    ),
                    ("number", self.archived_course.number),
                    ("org", self.archived_course.org),
                    ("rerun_link", f'/course_rerun/{str(self.archived_course.id)}'),
                    ("run", self.archived_course.id.run),
                    ("url", f'/course/{str(self.archived_course.id)}'),
                    ("is_active", False),
                ]),
            ],
            "in_process_course_actions": [],
        }
        expected_response = OrderedDict([
            ('count', 2),
            ('num_pages', 1),
            ('next', None),
            ('previous', None),
            ('results', expected_data),
        ])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    @override_waffle_switch(ENABLE_GLOBAL_STAFF_OPTIMIZATION, True)
    def test_org_query_if_passed(self):
        """Get list of courses when org filter passed as a query param.

        Expected result:
        - A list of courses available to the logged in user for the specified org.
        """
        response = self.client.get(self.api_v2_url, {"org": "demo-org"})

        self.assertEqual(len(response.data['results']['courses']), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_waffle_switch(ENABLE_GLOBAL_STAFF_OPTIMIZATION, True)
    def test_org_query_if_empty(self):
        """Get home page with an empty org query param.

        Expected result:
        - An empty list of courses available to the logged in user.
        """
        response = self.client.get(self.api_v2_url)

        self.assertEqual(len(response.data['results']['courses']), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_active_only_query_if_passed(self):
        """Get list of active courses only.

        Expected result:
        - A list of active courses available to the logged in user.
        """
        response = self.client.get(self.api_v2_url, {"active_only": "true"})

        self.assertEqual(len(response.data["results"]["courses"]), 1)
        self.assertEqual(response.data["results"]["courses"], [OrderedDict([
            ("course_key", str(self.course.id)),
            ("display_name", self.course.display_name),
            ("lms_link", f'//{settings.LMS_BASE}/courses/{str(self.course.id)}/jump_to/{self.course.location}'),
            ("cms_link", f'//{settings.CMS_BASE}{reverse_course_url("course_handler", self.course.id)}'),
            ("number", self.course.number),
            ("org", self.course.org),
            ("rerun_link", f'/course_rerun/{str(self.course.id)}'),
            ("run", self.course.id.run),
            ("url", f'/course/{str(self.course.id)}'),
            ("is_active", True),
        ])])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_archived_only_query_if_passed(self):
        """Get list of archived courses only.

        Expected result:
        - A list of archived courses available to the logged in user.
        """
        response = self.client.get(self.api_v2_url, {"archived_only": "true"})

        self.assertEqual(len(response.data["results"]["courses"]), 1)
        self.assertEqual(response.data["results"]["courses"], [OrderedDict([
            ("course_key", str(self.archived_course.id)),
            ("display_name", self.archived_course.display_name),
            (
                "lms_link",
                f'//{settings.LMS_BASE}/courses/{str(self.archived_course.id)}/jump_to/{self.archived_course.location}',
            ),
            ("cms_link", f'//{settings.CMS_BASE}{reverse_course_url("course_handler", self.archived_course.id)}'),
            ("number", self.archived_course.number),
            ("org", self.archived_course.org),
            ("rerun_link", f'/course_rerun/{str(self.archived_course.id)}'),
            ("run", self.archived_course.id.run),
            ("url", f'/course/{str(self.archived_course.id)}'),
            ("is_active", False),
        ])])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_query_if_passed(self):
        """Get list of courses when search filter passed as a query param.

        Expected result:
        - A list of courses (active or inactive) available to the logged in user for the specified search.
        """
        response = self.client.get(self.api_v2_url, {"search": "sample"})

        self.assertEqual(len(response.data["results"]["courses"]), 1)
        self.assertEqual(response.data["results"]["courses"], [OrderedDict([
            ("course_key", str(self.archived_course.id)),
            ("display_name", self.archived_course.display_name),
            (
                "lms_link",
                f'//{settings.LMS_BASE}/courses/{str(self.archived_course.id)}/jump_to/{self.archived_course.location}',
            ),
            ("cms_link", f'//{settings.CMS_BASE}{reverse_course_url("course_handler", self.archived_course.id)}'),
            ("number", self.archived_course.number),
            ("org", self.archived_course.org),
            ("rerun_link", f'/course_rerun/{str(self.archived_course.id)}'),
            ("run", self.archived_course.id.run),
            ("url", f'/course/{str(self.archived_course.id)}'),
            ("is_active", False),
        ])])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_query_if_passed(self):
        """Get list of courses when order filter passed as a query param.

        Expected result:
        - A list of courses (active or inactive) available to the logged in user for the specified order.
        """
        response = self.client.get(self.api_v2_url, {"order": "org"})

        self.assertEqual(len(response.data["results"]["courses"]), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"]["courses"][0]["org"], "demo-org")

    def test_page_query_if_passed(self):
        """Get list of courses when page filter passed as a query param.

        Expected result:
        - A list of courses (active or inactive) available to the logged in user for the specified page.
        """
        response = self.client.get(self.api_v2_url, {"page": 1})

        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("cms.djangoapps.contentstore.views.course.CourseOverview")
    @patch("cms.djangoapps.contentstore.views.course.modulestore")
    def test_api_v2_is_disabled(self, mock_modulestore, mock_course_overview):
        """Get list of courses when home page course v2 API is disabled.

        Expected result:
        - Courses are read from the modulestore.
        """
        with override_settings(FEATURES={'ENABLE_HOME_PAGE_COURSE_API_V2': False}):
            response = self.client.get(self.api_v1_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_modulestore().get_course_summaries.assert_called_once()
        mock_course_overview.get_all_courses.assert_not_called()
