"""
Tests for Learner Recommendations views and related functions.
"""

import json
from django.urls import reverse_lazy
from edx_toggles.toggles.testutils import override_waffle_flag
from rest_framework.test import APITestCase
from unittest import mock

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.learner_recommendations.toggles import (
    ENABLE_COURSE_ABOUT_PAGE_RECOMMENDATIONS,
)


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


@override_waffle_flag(ENABLE_COURSE_ABOUT_PAGE_RECOMMENDATIONS, active=True)
class TestAmplitudeRecommendationsView(APITestCase):
    """Unit tests for the Amplitude recommendations API"""

    url = reverse_lazy(
        "learner_recommendations:amplitude_recommendations",
        kwargs={'course_id': 'course-v1:test+TestX+Test_Course'}
    )

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="test")
        self.recommended_courses = [
            "MITx+6.00.1x",
            "IBM+PY0101EN",
            "HarvardX+CS50P",
            "UQx+IELTSx",
            "HarvardX+CS50x",
            "Harvard+CS50z",
            "BabsonX+EPS03x",
            "TUMx+QPLS2x",
            "NYUx+FCS.NET.1",
            "MichinX+101x",
        ]

    def _get_filtered_courses(self):
        """
        Returns the filtered course data
        """
        filtered_course = []
        for course_key in self.recommended_courses:
            filtered_course.append({
                "key": course_key,
                "uuid": "4f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
                "title": f"Title for {course_key}",
                "image": {
                    "src": "https://www.logo_image_url.com",
                },
                "url_slug": "https://www.marketing_url.com",
                "owners": [
                    {
                        "key": "org-1",
                        "name": "org 1",
                        "logo_image_url": "https://discovery.com/organization/logos/org-1.png",
                    },
                    {
                        "key": "org-2",
                        "name": "org 2",
                        "logo_image_url": "https://discovery.com/organization/logos/org-2.png",
                    }
                ],
                "course_runs": [
                    {
                        "key": "course-v1:Test+2023_T1",
                        "marketing_url": "https://www.marketing_url.com",
                        "availability": "Current",
                    },
                    {
                        "key": "course-v1:Test+2023_T2",
                        "marketing_url": "https://www.marketing_url.com",
                        "availability": "Upcoming",
                    }
                ]
            })

        return filtered_course

    @override_waffle_flag(ENABLE_COURSE_ABOUT_PAGE_RECOMMENDATIONS, active=False)
    def test_waffle_flag_off(self):
        """
        Verify API returns 404 (Not Found) if waffle flag is off.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, None)

    @mock.patch('lms.djangoapps.learner_recommendations.views.is_enterprise_learner', mock.Mock(return_value=True))
    def test_enterprise_user_access(self):
        """
        Verify API returns 403 (Forbidden) for an enterprise user.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations",
        mock.Mock(side_effect=Exception),
    )
    def test_amplitude_api_unexpected_error(self):
        """
        Test that if the Amplitude API gives an unexpected error,
        API returns 404 (Not Found).
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, None)

    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_recommendations.views.filter_recommended_courses")
    def test_successful_response(
        self, filter_recommended_courses_mock, get_amplitude_course_recommendations_mock
    ):
        """
        Verify API returns course recommendations.
        """
        expected_recommendations_length = 4
        filter_recommended_courses_mock.return_value = self._get_filtered_courses()
        get_amplitude_course_recommendations_mock.return_value = [
            False,
            True,
            self.recommended_courses,
        ]

        response = self.client.get(self.url)
        response_content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_content.get("isControl"), False)
        self.assertEqual(
            len(response_content.get("courses")), expected_recommendations_length
        )
