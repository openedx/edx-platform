""" Test Recommendations helpers methods """
import ddt
from django.test import TestCase
from unittest.mock import Mock, patch

from common.djangoapps.student.tests.factories import (
    CourseEnrollmentFactory,
    UserFactory,
)
from lms.djangoapps.learner_recommendations.utils import (
    filter_recommended_courses,
    get_amplitude_course_recommendations,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@ddt.ddt
class TestRecommendationsHelper(TestCase):
    """Test course recommendations helper methods."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    @ddt.data(
        ({}, 0),
        ({"userData": {}}, 0),
        ({"userData": {"recommendations": []}}, 0),
        (
            {
                "userData": {
                    "recommendations": [
                        {
                            "items": ["MITx+6.00.1x", "IBM+PY0101EN", "HarvardX+CS50P"],
                            "is_control": True,
                            "has_is_control": False,
                        }
                    ],
                }
            },
            3,
        ),
    )
    @patch("lms.djangoapps.learner_recommendations.utils.requests.get")
    @ddt.unpack
    def test_get_amplitude_course_recommendations_method(
        self, mocked_response, expected_recommendations_count, mock_get
    ):
        """
        Tests the get_amplitude_recommendations method returns course key list.
        """
        mock_get.return_value = Mock(status_code=200, json=lambda: mocked_response)
        _, _, course_keys = get_amplitude_course_recommendations(
            self.user.id, "amplitude-rec-id"
        )
        self.assertEqual(len(course_keys), expected_recommendations_count)


class TestFilterRecommendedCourses(ModuleStoreTestCase):
    """Test for filter_recommended_courses helper method."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course_data = {
            "course_key": "Mocked course key",
            "title": "Mocked course title",
            "owners": [{"logo_image_url": "https://www.logo_image_url.com"}],
            "marketing_url": "https://www.marketing_url.com",
        }
        self.recommended_course_keys = [
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

    @patch("lms.djangoapps.learner_recommendations.utils.get_course_data")
    def test_enrolled_courses_are_removed_from_recommendations(
        self, mocked_get_course_data
    ):
        """
        Tests that given a recommended course list, the filter_recommended_courses
        method removes the enrolled courses from it.
        """
        total_enrolled_courses = 6
        total_recommendations = len(self.recommended_course_keys)
        mocked_get_course_data.return_value = self.course_data
        for course_run_key in self.course_run_keys[:total_enrolled_courses]:
            CourseEnrollmentFactory(course_id=course_run_key, user=self.user)

        filtered_courses = filter_recommended_courses(
            self.user, self.recommended_course_keys, total_recommendations
        )
        self.assertEqual(len(filtered_courses), total_recommendations - total_enrolled_courses)
