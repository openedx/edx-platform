"""
Tests for Course Recommendations
"""

import json
from unittest import mock
from unittest.mock import Mock

import ddt
from django.urls import reverse_lazy
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from lms.djangoapps.learner_home.test_utils import (
    random_url,
)
from lms.djangoapps.learner_home.recommendations.waffle import (
    ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS,
)
from xmodule.modulestore.tests.django_utils import (
    SharedModuleStoreTestCase,
)


@ddt.ddt
class TestCourseRecommendationApiView(SharedModuleStoreTestCase):
    """Unit tests for the course recommendations on learner home page."""

    password = "test"
    url = reverse_lazy("learner_home:courses")

    GENERAL_RECOMMENDATIONS = [
        {
            "course_key": "HogwartsX+6.00.1x",
            "logo_image_url": random_url(),
            "marketing_url": random_url(),
            "title": "Defense Against the Dark Arts",
        },
        {
            "course_key": "MonstersX+SC101EN",
            "logo_image_url": random_url(),
            "marketing_url": random_url(),
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
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=self.password)
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
        self.course_run_keys = [
            "course-v1:MITx+6.00.1x+Run_0",
            "course-v1:IBM+PY0101EN+Run_0",
            "course-v1:HarvardX+CS50P+Run_0",
            "course-v1:UQx+IELTSx+Run_0",
            "course-v1:HarvardX+CS50x+Run_0",
            "course-v1:Harvard+CS50z+Run_0",
            "course-v1:BabsonX+EPS03x+Run_0",
            "course-v1:TUMx+QPLS2x+Run_0",
            "course-v1:NYUx+FCS.NET.1+Run_0",
            "course-v1:MichinX+101x+Run_0",
        ]
        self.course_data = {
            "course_key": "MITx+6.00.1x",
            "title": "Introduction to Computer Science and Programming Using Python",
            "owners": [{"logo_image_url": "https://www.logo_image_url.com"}],
            "marketing_url": "https://www.marketing_url.com",
        }

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=False)
    def test_waffle_flag_off(self):
        """
        Verify API returns 404 if waffle flag is off.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, None)

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations"
    )
    def test_no_recommendations_from_amplitude(
        self, mocked_get_personalized_course_recommendations
    ):
        """
        Verify API returns general recommendations if no course recommendations from amplitude.
        """
        mocked_get_personalized_course_recommendations.return_value = [False, True, []]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isPersonalizedRecommendation"), False)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations",
        Mock(side_effect=Exception),
    )
    def test_amplitude_api_unexpected_error(self):
        """
        Test that if the Amplitude API gives an unexpected error, general recommendations are returned.
        """

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isPersonalizedRecommendation"), False)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_home.recommendations.views.get_course_data")
    def test_get_course_recommendations(
        self, mocked_get_course_data, mocked_get_personalized_course_recommendations
    ):
        """
        Verify API returns course recommendations.
        """
        mocked_get_personalized_course_recommendations.return_value = [
            False,
            True,
            self.recommended_courses,
        ]
        mocked_get_course_data.return_value = self.course_data
        expected_recommendations_length = 5

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isPersonalizedRecommendation"), True)
        self.assertEqual(
            len(response_content.get("courses")), expected_recommendations_length
        )

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations"
    )
    def test_general_recommendations(
        self, mocked_get_personalized_course_recommendations
    ):
        """
        Test that a user gets general recommendations for the control group.
        """
        mocked_get_personalized_course_recommendations.return_value = [
            True,
            True,
            self.recommended_courses,
        ]

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isPersonalizedRecommendation"), False)
        self.assertEqual(
            response_content.get("courses"),
            self.SERIALIZED_GENERAL_RECOMMENDATIONS,
        )

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_home.recommendations.views.get_course_data")
    def test_get_enrollable_course_recommendations(
        self, mocked_get_course_data, mocked_get_personalized_course_recommendations
    ):
        """
        Verify API returns course recommendations for courses in which user is not enrolled.
        """
        mocked_get_personalized_course_recommendations.return_value = [
            False,
            True,
            self.recommended_courses,
        ]
        mocked_get_course_data.return_value = self.course_data
        expected_recommendations = 4
        # enrolling in 6 courses
        for course_run_key in self.course_run_keys[:6]:
            CourseEnrollmentFactory(course_id=course_run_key, user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isPersonalizedRecommendation"), True)
        self.assertEqual(len(response_content.get("courses")), expected_recommendations)

    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @mock.patch("django.conf.settings.GENERAL_RECOMMENDATIONS", GENERAL_RECOMMENDATIONS)
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations"
    )
    @mock.patch("lms.djangoapps.learner_home.recommendations.views.get_course_data")
    def test_no_enrollable_course(
        self, mocked_get_course_data, mocked_get_personalized_course_recommendations
    ):
        """
        Test that if after filtering already enrolled courses from Amplitude recommendations
        we are left with zero personalized recommendations, we return general recommendations.
        """
        mocked_get_personalized_course_recommendations.return_value = [
            False,
            True,
            self.recommended_courses,
        ]
        mocked_get_course_data.return_value = self.course_data

        # Enrolling in all courses
        for course_run_key in self.course_run_keys:
            CourseEnrollmentFactory(course_id=course_run_key, user=self.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        response_content = json.loads(response.content)
        self.assertEqual(response_content.get("isPersonalizedRecommendation"), False)
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
    @mock.patch("lms.djangoapps.learner_home.recommendations.views.segment.track")
    @mock.patch("lms.djangoapps.learner_home.recommendations.views.get_course_data")
    @mock.patch(
        "lms.djangoapps.learner_home.recommendations.views.get_personalized_course_recommendations"
    )
    @override_waffle_flag(ENABLE_LEARNER_HOME_AMPLITUDE_RECOMMENDATIONS, active=True)
    @ddt.unpack
    def test_recommendations_viewed_segment_event(
        self,
        is_control,
        has_is_control,
        expected_is_control,
        mocked_get_personalized_course_recommendations,
        mocked_get_course_data,
        segment_track_mock
    ):
        """
        Test that Segment event is emitted with desired properties.
        """
        mocked_get_personalized_course_recommendations.return_value = [
            is_control,
            has_is_control,
            self.recommended_courses,
        ]
        mocked_get_course_data.return_value = self.course_data
        self.client.get(self.url)

        assert segment_track_mock.call_count == 1
        assert segment_track_mock.call_args[0][1] == "edx.bi.user.recommendations.viewed"
        self.assertEqual(segment_track_mock.call_args[0][2]["is_control"], expected_is_control)
