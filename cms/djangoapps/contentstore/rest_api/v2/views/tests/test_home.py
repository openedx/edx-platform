"""
Unit tests for home page view.
"""
import ddt
from django.conf import settings
from django.urls import reverse
from collections import OrderedDict
from edx_toggles.toggles.testutils import (
    override_waffle_switch,
)
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.views.course import ENABLE_GLOBAL_STAFF_OPTIMIZATION
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.factories import CourseFactory
from cms.djangoapps.contentstore.utils import get_lms_link_for_item, reverse_course_url


@ddt.ddt
class HomePageCoursesViewV2Test(CourseTestCase):
    """
    Tests for HomePageView view version 2.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("cms.djangoapps.contentstore:v2:courses")
        CourseOverviewFactory.create(
            id=self.course.id,
            org=self.course.org,
            run=self.course.id.run,
            display_name=self.course.display_name,
        )

    def test_home_page_response(self):
        """Get list of courses available to the logged in user.

        Expected result:
        - A list of courses available to the logged in user.
        - A paginated response.
        """
        response = self.client.get(self.url)
        course_id = str(self.course.id)

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
            ])],
            "in_process_course_actions": [],
        }
        expected_response = OrderedDict([
            ('count', 1),
            ('num_pages', 1),
            ('next', None),
            ('previous',None),
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
        demo_course_key = self.store.make_course_key('demo-org', 'demo-number', 'demo-run')
        CourseOverviewFactory.create(id=demo_course_key, org=demo_course_key.org)

        response = self.client.get(self.url, {"org": "demo-org"})

        self.assertEqual(len(response.data['results']['courses']), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_waffle_switch(ENABLE_GLOBAL_STAFF_OPTIMIZATION, True)
    def test_org_query_if_empty(self):
        """Test home page with an empty org query param"""
        response = self.client.get(self.url)

        self.assertEqual(len(response.data['results']['courses']), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
