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
        for course_key in self.recommended_courses[0:4]:
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

    @mock.patch("lms.djangoapps.learner_dashboard.api.v0.views.segment.track")
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_recommendations.views.filter_recommended_courses")
    def test_successful_response(
        self, filter_recommended_courses_mock, get_amplitude_course_recommendations_mock, segment_mock,
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
        segment_mock.return_value = None

        response = self.client.get(self.url)
        response_content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_content.get("isControl"), False)
        self.assertEqual(
            len(response_content.get("courses")), expected_recommendations_length
        )

        # Verify that the segment event was fired
        assert segment_mock.call_count == 1
        assert segment_mock.call_args[0][1] == "edx.bi.user.recommendations.viewed"


@override_waffle_flag(ENABLE_COURSE_ABOUT_PAGE_RECOMMENDATIONS, active=True)
class TestCrossProductRecommendationsView(APITestCase):
    """Unit tests for the Cross Product Recommendations View"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password="test")
        self.courses = [
            {
                "key": "ColumbiaX+BC24FNTC",
                "uuid": "5f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
                "title": f"Title 1",
                "image": {
                        "src": "https://www.logo_image_url.com",
                },
                "url_slug": "https://www.marketing_url.com",
                "course_type": "bootcamp-2u",
                "owners": [
                    {
                            "key": "org-1",
                            "name": "org 1",
                            "logo_image_url": "https://discovery.com/organization/logos/org-1.png",
                    },
                ],
                "course_runs": [
                    {
                        "key": "course-v1:Test+2023_T2",
                        "marketing_url": "https://www.marketing_url.com",
                        "availability": "Current",
                    }
                ],
                "location_restriction": {
                    "restriction_type": "blocklist",
                    "countries": ["CN"],
                    "states": []
                }
            },
            {
                "key": "MITx+BLN",
                "uuid": "6f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
                "title": f"Title 2",
                "image": {
                        "src": "https://www.logo_image_url.com",
                },
                "url_slug": "https://www.marketing_url.com",
                "course_type": "executive-education",
                "owners": [
                    {
                            "key": "org-1",
                            "name": "org 1",
                            "logo_image_url": "https://discovery.com/organization/logos/org-1.png",
                    },
                ],
                "course_runs": [
                    {
                        "key": "course-v1:Test+2023_T2",
                        "marketing_url": "https://www.marketing_url.com",
                        "availability": "Current",
                    }
                ],
                "location_restriction": None
            },
        ]

    def _get_url(self, course_key):
        return reverse_lazy(
            "learner_recommendations:cross_product_recommendations",
            kwargs={'course_id': f'course-v1:{course_key}+Test_Course'}
        )

    @mock.patch("lms.djangoapps.learner_recommendations.views.get_course_data")
    @mock.patch("lms.djangoapps.learner_recommendations.views.country_code_from_ip")
    def test_successful_response(
        self, country_code_from_ip_mock, get_course_data_mock,
    ):
        """
        Verify cross product course recommendations are returned.
        """
        country_code_from_ip_mock.return_value = "za"
        get_course_data_mock.side_effect = [self.courses[0], self.courses[1]]

        response = self.client.get(self._get_url('HKUx+FinTechT1x'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 2)

    @mock.patch("lms.djangoapps.learner_recommendations.views.get_course_data")
    @mock.patch("lms.djangoapps.learner_recommendations.views.country_code_from_ip")
    def test_response_with_country_restriction(
        self, country_code_from_ip_mock, get_course_data_mock,
    ):
        """
        Verify cross product course recommendations are returned.
        """
        country_code_from_ip_mock.return_value = "cn"
        get_course_data_mock.side_effect = [self.courses[0], self.courses[1]]

        response = self.client.get(self._get_url('HKUx+FinTechT1x'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 1)
        self.assertEqual(course_data[0]["title"], "Title 2")
        self.assertEqual(course_data[0]["courseType"], "executive-education")

    def test_empty_response(self):
        """
        Verify an empty array our courses is returned if there are no associated courses.
        """
        response = self.client.get(self._get_url('No+Associations'))
        response_content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_content), 0)
