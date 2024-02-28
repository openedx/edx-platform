"""
Unit tests for home page view.
"""
import ddt
from django.conf import settings
from django.urls import reverse
from edx_toggles.toggles.testutils import (
    override_waffle_switch,
)
from rest_framework import status

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.views.course import ENABLE_GLOBAL_STAFF_OPTIMIZATION
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class HomePageCoursesViewTest(CourseTestCase):
    """
    Tests for HomePageView.
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("cms.djangoapps.contentstore:v2:courses")

    def test_home_page_response(self):
        """Check successful response content"""
        response = self.client.get(self.url)
        course_id = str(self.course.id)

        expected_response = {
            "courses": [{
                "course_key": course_id,
                "display_name": self.course.display_name,
                "lms_link": f'//{settings.LMS_BASE}/courses/{course_id}/jump_to/{self.course.location}',
                "number": self.course.number,
                "org": self.course.org,
                "rerun_link": f'/course_rerun/{course_id}',
                "run": self.course.id.run,
                "url": f'/course/{course_id}',
            }],
            "in_process_course_actions": [],
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_response, response.data)

    @override_waffle_switch(ENABLE_GLOBAL_STAFF_OPTIMIZATION, True)
    def test_org_query_if_passed(self):
        """Test home page when org filter passed as a query param"""
        foo_course = self.store.make_course_key('foo-org', 'bar-number', 'baz-run')
        test_course = CourseFactory.create(
            org=foo_course.org,
            number=foo_course.course,
            run=foo_course.run
        )
        CourseOverviewFactory.create(id=test_course.id, org='foo-org')
        response = self.client.get(self.url, {"org": "foo-org"})
        self.assertEqual(len(response.data['courses']), 1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_waffle_switch(ENABLE_GLOBAL_STAFF_OPTIMIZATION, True)
    def test_org_query_if_empty(self):
        """Test home page with an empty org query param"""
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['courses']), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
