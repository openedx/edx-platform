"""
Tests for Learner Recommendations views and related functions.
"""

import json
from django.urls import reverse_lazy
from edx_toggles.toggles.testutils import override_waffle_flag
from rest_framework.test import APITestCase
from unittest import mock

import ddt
from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.student.toggles import ENABLE_FALLBACK_RECOMMENDATIONS
from lms.djangoapps.learner_recommendations.toggles import (
    ENABLE_COURSE_ABOUT_PAGE_RECOMMENDATIONS,
    ENABLE_DASHBOARD_RECOMMENDATIONS,
)
from lms.djangoapps.learner_recommendations.tests.test_data import mock_cross_product_recommendation_keys


class TestRecommendationsBase(APITestCase):
    """Recommendations test base class"""

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


@override_waffle_flag(ENABLE_COURSE_ABOUT_PAGE_RECOMMENDATIONS, active=True)
class TestAboutPageRecommendationsView(TestRecommendationsBase):
    """Unit tests for the Amplitude recommendations API"""

    url = reverse_lazy(
        "learner_recommendations:amplitude_recommendations",
        kwargs={'course_id': 'course-v1:test+TestX+Test_Course'}
    )

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


class TestCrossProductRecommendationsView(APITestCase):
    """Unit tests for the Cross Product Recommendations View"""

    def setUp(self):
        super().setUp()
        self.associated_course_keys = ["edx+HL1", "edx+HL2"]

    def _get_url(self, course_key):
        """
        Returns the url with a sepcific course id
        """
        return reverse_lazy(
            "learner_recommendations:cross_product_recommendations",
            kwargs={'course_id': f'course-v1:{course_key}+Test_Course'}
        )

    def _get_recommended_courses(self, num_of_courses_with_restriction=0):
        """
        Returns an array of 2 discovery courses with or without country restrictions
        """
        courses = []
        restriction_obj = {
            "restriction_type": "blocklist",
            "countries": ["CN"],
            "states": []
        }

        for course_key in enumerate(self.associated_course_keys):
            location_restriction = restriction_obj if num_of_courses_with_restriction > 0 else None

            courses.append({
                "key": course_key[1],
                "uuid": "6f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
                "title": f"Title {course_key[0]}",
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
                "location_restriction": location_restriction
            })

            if num_of_courses_with_restriction > 0:
                num_of_courses_with_restriction -= 1

        return courses

    @mock.patch("django.conf.settings.CROSS_PRODUCT_RECOMMENDATIONS_KEYS", mock_cross_product_recommendation_keys)
    @mock.patch("lms.djangoapps.learner_recommendations.views.get_course_data")
    @mock.patch("lms.djangoapps.learner_recommendations.views.country_code_from_ip")
    def test_successful_response(
        self, country_code_from_ip_mock, get_course_data_mock,
    ):
        """
        Verify 2 cross product course recommendations are returned.
        """
        country_code_from_ip_mock.return_value = "za"
        mock_course_data = self._get_recommended_courses()
        get_course_data_mock.side_effect = [mock_course_data[0], mock_course_data[1]]

        response = self.client.get(self._get_url('edx+HL0'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 2)

    @mock.patch("django.conf.settings.CROSS_PRODUCT_RECOMMENDATIONS_KEYS", mock_cross_product_recommendation_keys)
    @mock.patch("lms.djangoapps.learner_recommendations.views.get_course_data")
    @mock.patch("lms.djangoapps.learner_recommendations.views.country_code_from_ip")
    def test_one_course_country_restriction_response(
        self, country_code_from_ip_mock, get_course_data_mock,
    ):
        """
        Verify 1 cross product course recommendation is returned
        if there is a location restriction for one course for the users country
        """
        country_code_from_ip_mock.return_value = "cn"
        mock_course_data = self._get_recommended_courses(1)
        get_course_data_mock.side_effect = [mock_course_data[0], mock_course_data[1]]

        response = self.client.get(self._get_url('edx+HL0'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 1)
        self.assertEqual(course_data[0]["title"], "Title 1")

    @mock.patch("django.conf.settings.CROSS_PRODUCT_RECOMMENDATIONS_KEYS", mock_cross_product_recommendation_keys)
    @mock.patch("lms.djangoapps.learner_recommendations.views.get_course_data")
    @mock.patch("lms.djangoapps.learner_recommendations.views.country_code_from_ip")
    def test_both_course_country_restriction_response(
        self, country_code_from_ip_mock, get_course_data_mock,
    ):
        """
        Verify no courses are returned if both courses have a location restriction
        for the users country.
        """
        country_code_from_ip_mock.return_value = "cn"
        mock_course_data = self._get_recommended_courses(2)

        get_course_data_mock.side_effect = [mock_course_data[0], mock_course_data[1]]

        response = self.client.get(self._get_url('edx+HL0'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 0)

    @mock.patch("django.conf.settings.CROSS_PRODUCT_RECOMMENDATIONS_KEYS", mock_cross_product_recommendation_keys)
    def test_no_associated_course_response(self):
        """
        Verify an empty array of courses is returned if there are no associated course keys.
        """
        response = self.client.get(self._get_url('No+Associations'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 0)

    @mock.patch("django.conf.settings.CROSS_PRODUCT_RECOMMENDATIONS_KEYS", mock_cross_product_recommendation_keys)
    @mock.patch("lms.djangoapps.learner_recommendations.views.get_course_data")
    @mock.patch("lms.djangoapps.learner_recommendations.views.country_code_from_ip")
    def test_no_response_from_discovery(self, country_code_from_ip_mock, get_course_data_mock):
        """
        Verify an empty array of courses is returned if discovery returns two empty dictionaries.
        """
        country_code_from_ip_mock.return_value = "za"
        get_course_data_mock.side_effect = [{}, {}]

        response = self.client.get(self._get_url('edx+HL0'))
        response_content = json.loads(response.content)
        course_data = response_content["courses"]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(course_data), 0)


@ddt.ddt
class TestDashboardRecommendationsApiView(TestRecommendationsBase):
    """Unit tests for the course recommendations on learner home page."""

    url = reverse_lazy("learner_recommendations:courses")

    GENERAL_RECOMMENDATIONS = [
        {
            "course_key": "HogwartsX+6.00.1x",
            "logo_image_url": "http://edx.org/images/test.png",
            "marketing_url": "http://edx.org/courses/AI",
            "title": "Defense Against the Dark Arts",
        },
        {
            "course_key": "MonstersX+SC101EN",
            "logo_image_url": "http://edx.org/images/test.png",
            "marketing_url": "http://edx.org/courses/AI",
            "title": "Scaring 101",
        },
    ]

    SERIALIZED_GENERAL_RECOMMENDATIONS = [
        {
            "courseKey": GENERAL_RECOMMENDATIONS[0]["course_key"],
            "logoImageUrl": GENERAL_RECOMMENDATIONS[0]["logo_image_url"],
            "marketingUrl": GENERAL_RECOMMENDATIONS[0]["marketing_url"],
            "title": GENERAL_RECOMMENDATIONS[0]["title"],
        },
        {
            "courseKey": GENERAL_RECOMMENDATIONS[1]["course_key"],
            "logoImageUrl": GENERAL_RECOMMENDATIONS[1]["logo_image_url"],
            "marketingUrl": GENERAL_RECOMMENDATIONS[1]["marketing_url"],
            "title": GENERAL_RECOMMENDATIONS[1]["title"],
        },
    ]

    def setUp(self):
        super().setUp()
        self.course_run_keys = [f"course-v1:{course}+Run_0" for course in self.recommended_courses]

    def _get_filtered_courses(self):
        """
        Returns the filtered course data
        """
        filtered_course = []
        for course_key in self.recommended_courses[:5]:
            filtered_course.append({
                "key": course_key,
                "title": f"Title for {course_key}",
                "logo_image_url": "https://www.logo_image_url.com",
                "marketing_url": "https://www.marketing_url.com",
            })

        return filtered_course

    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=False)
    def test_waffle_flag_off(self):
        """
        Verify API returns 404 if waffle flag is off.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, None)

    @override_waffle_flag(ENABLE_FALLBACK_RECOMMENDATIONS, active=True)
    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    def test_no_recommendations_from_amplitude(
        self, get_amplitude_course_recommendations_mock
    ):
        """
        Verify API returns general recommendations if no course recommendations from amplitude.
        """
        get_amplitude_course_recommendations_mock.return_value = [False, True, []]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), False)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @override_waffle_flag(ENABLE_FALLBACK_RECOMMENDATIONS, active=True)
    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations",
        mock.Mock(side_effect=Exception),
    )
    def test_amplitude_api_unexpected_error(self):
        """
        Test that if the Amplitude API gives an unexpected error, general recommendations are returned.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), None)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_recommendations.views.filter_recommended_courses")
    def test_get_course_recommendations(
        self, filter_recommended_courses_mock, get_amplitude_course_recommendations_mock
    ):
        """
        Verify API returns course recommendations.
        """
        get_amplitude_course_recommendations_mock.return_value = [
            False,
            True,
            self.recommended_courses,
        ]

        filter_recommended_courses_mock.return_value = self._get_filtered_courses()
        expected_recommendations_length = 5

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), False)
        self.assertEqual(
            len(response_content.get("courses")), expected_recommendations_length
        )

    @override_waffle_flag(ENABLE_FALLBACK_RECOMMENDATIONS, active=True)
    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    def test_general_recommendations(
        self, get_amplitude_course_recommendations_mock
    ):
        """
        Test that a user gets general recommendations for the control group.
        """
        get_amplitude_course_recommendations_mock.return_value = [
            True,
            True,
            self.recommended_courses,
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), True)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @override_waffle_flag(ENABLE_FALLBACK_RECOMMENDATIONS, active=False)
    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    def test_fallback_recommendations_disabled(
        self, get_amplitude_course_recommendations_mock
    ):
        """
        Test that a user gets no recommendations for the control group.
        """
        get_amplitude_course_recommendations_mock.return_value = [
            True,
            True,
            [],
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), True)
        self.assertEqual(response_content.get("courses"), [])

    @override_waffle_flag(ENABLE_FALLBACK_RECOMMENDATIONS, active=True)
    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_recommendations.views.filter_recommended_courses")
    def test_no_recommended_courses_after_filtration(
        self, filter_recommended_courses_mock, get_amplitude_course_recommendations_mock
    ):
        """
        Test that if after filtering already enrolled courses from Amplitude recommendations
        we are left with zero personalized recommendations, we return general recommendations.
        """
        filter_recommended_courses_mock.return_value = []
        get_amplitude_course_recommendations_mock.return_value = [
            False,
            True,
            self.recommended_courses,
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), False)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @ddt.data(
        (True, False, None),
        (False, True, False),
        (False, False, None),
        (True, True, True),
    )
    @mock.patch("lms.djangoapps.learner_recommendations.views.segment.track")
    @mock.patch("lms.djangoapps.learner_recommendations.views.filter_recommended_courses")
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.get_amplitude_course_recommendations"
    )
    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @ddt.unpack
    def test_recommendations_viewed_segment_event(
        self,
        is_control,
        has_is_control,
        expected_is_control,
        get_amplitude_course_recommendations_mock,
        filter_recommended_courses_mock,
        segment_track_mock
    ):
        """
        Test that Segment event is emitted with desired properties.
        """
        get_amplitude_course_recommendations_mock.return_value = [
            is_control,
            has_is_control,
            self.recommended_courses,
        ]
        filter_recommended_courses_mock.return_value = self._get_filtered_courses()
        self.client.get(self.url)

        assert segment_track_mock.call_count == 1
        assert segment_track_mock.call_args[0][1] == "edx.bi.user.recommendations.viewed"
        self.assertEqual(segment_track_mock.call_args[0][2]["is_control"], expected_is_control)

    @override_waffle_flag(ENABLE_DASHBOARD_RECOMMENDATIONS, active=True)
    @mock.patch(
        "lms.djangoapps.learner_recommendations.views.is_user_enrolled_in_ut_austin_masters_program"
    )
    def test_no_recommendations_for_masters_program_learners(
        self, is_user_enrolled_in_ut_austin_masters_program_mock
    ):
        """
        Verify API returns no recommendations if a user is enrolled in UT Austin masters program.
        """
        is_user_enrolled_in_ut_austin_masters_program_mock.return_value = True

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isControl"), None)
        self.assertEqual(response_content.get("courses"), [])
