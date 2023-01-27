"""
Tests for Learner Recommendations views and related functions.
"""

import json
from unittest import mock

from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from common.djangoapps.student.tests.factories import UserFactory


class TestAlgoliaCoursesSearchView(APITestCase):
    """Unit tests for the Algolia courses recommendation."""

    password = "test"
    view_url = reverse_lazy(
        "learner_recommendations:algolia_courses",
        kwargs={'course_id': 'course-v1:test+TestX+Test_Course'}
    )

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.expected_courses_recommendation = {
            "hits": [
                {
                    "availability": ["Available now"],
                    "level": ["Introductory"],
                    "marketing_url": "https://marketing-site.com/course/monsters-anatomy-101",
                    "card_image_url": "https://card-site.com/course/monsters-anatomy-101",
                    "active_run_key": "course-v1:test+TestX+Test_Course_1",
                    "skills": [{"skill": "skill_1"}, {"skill": "skill_2"}],
                },
                {
                    "availability": ["Available now"],
                    "level": ["Intermediate"],
                    "marketing_url": "https://marketing-site.com/course/monsters-anatomy-101",
                    "card_image_url": "https://card-site.com/course/monsters-anatomy-101",
                    "active_run_key": "course-v1:test+TestX+Test_Course_2",
                    "skills": [{"skill": "skill_1"}, {"skill": "skill_2"}],
                }
            ],
            "nbHits": 2
        }

    def test_unauthenticated_request(self):
        """
        Test unauthenticated request to Algolia courses recommendation API view.
        """

        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 401)

    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_course_data"
    )
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_course_run_details"
    )
    def test_no_course_data(
        self,
        mocked_get_course_run_details,
        mocked_get_course_data
    ):
        """
        Verify API returns empty response if no course data found.
        """
        mocked_get_course_run_details.return_value = {"course": "edX+DemoX"}
        mocked_get_course_data.return_value = None

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("courses"), [])
        self.assertEqual(response_content.get("count"), 0)

    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_course_data"
    )
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_course_run_details"
    )
    def test_no_course_skill_names(
        self,
        mocked_get_course_run_details,
        mocked_get_course_data
    ):
        """
        Verify API returns empty response if no course skill_names found.
        """
        mocked_get_course_run_details.return_value = {"course": "edX+DemoX"}
        mocked_get_course_data.return_value = {"level_type": "Advanced", "skill_names": []}

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("courses"), [])
        self.assertEqual(response_content.get("count"), 0)

    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_algolia_courses_recommendation"
    )
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_course_run_details"
    )
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_course_data"
    )
    def test_recommendations(
        self,
        mocked_get_course_data,
        mocked_get_course_run_details,
        mocked_get_algolia_courses_recommendation
    ):
        """
        Verify API response structure.
        """
        mocked_get_course_run_details.return_value = {"course": "edX+DemoX"}
        mocked_get_course_data.return_value = {"level_type": "Advanced", "skill_names": ["skill_1", "skill_2"]}
        mocked_get_algolia_courses_recommendation.return_value = self.expected_courses_recommendation

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("courses"), self.expected_courses_recommendation["hits"])
        self.assertEqual(response_content.get("count"), self.expected_courses_recommendation["nbHits"])
