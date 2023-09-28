"""Tests for serializers for the Learner Recommendations"""

from uuid import uuid4

from django.test import TestCase

from lms.djangoapps.learner_recommendations.serializers import (
    DashboardRecommendationsSerializer,
    RecommendationsContextSerializer,
    CrossProductRecommendationsSerializer,
    CrossProductAndAmplitudeRecommendationsSerializer,
    AmplitudeRecommendationsSerializer
)
from lms.djangoapps.learner_recommendations.tests.test_data import (
    mock_amplitude_and_cross_product_course_data,
    mock_cross_product_course_data,
    mock_amplitude_course_data
)


class TestDashboardRecommendationsSerializer(TestCase):
    """High-level tests for DashboardRecommendationsSerializer"""

    @classmethod
    def mock_recommended_courses(cls, courses_count=2):
        """Sample course data"""

        recommended_courses = []

        for _ in range(courses_count):
            recommended_courses.append(
                {
                    "course_key": str(uuid4()),
                    "logo_image_url": "http://edx.org/images/test.png",
                    "marketing_url": "http://edx.org/courses/AI",
                    "title": str(uuid4()),
                },
            )

        return recommended_courses

    def test_no_recommended_courses(self):
        """That that data serializes correctly for empty courses list"""

        recommended_courses = self.mock_recommended_courses(courses_count=0)

        output_data = DashboardRecommendationsSerializer(
            {
                "courses": recommended_courses,
            }
        ).data

        self.assertDictEqual(
            output_data,
            {
                "courses": [],
                "isControl": None,
            },
        )

    def test_happy_path(self):
        """Test that data serializes correctly"""

        recommended_courses = self.mock_recommended_courses()

        output_data = DashboardRecommendationsSerializer(
            {
                "courses": recommended_courses,
                "is_control": False,
            }
        ).data

        self.assertDictEqual(
            output_data,
            {
                "courses": [
                    {
                        "courseKey": recommended_courses[0]["course_key"],
                        "logoImageUrl": recommended_courses[0]["logo_image_url"],
                        "marketingUrl": recommended_courses[0]["marketing_url"],
                        "title": recommended_courses[0]["title"],
                    },
                    {
                        "courseKey": recommended_courses[1]["course_key"],
                        "logoImageUrl": recommended_courses[1]["logo_image_url"],
                        "marketingUrl": recommended_courses[1]["marketing_url"],
                        "title": recommended_courses[1]["title"],
                    },
                ],
                "isControl": False,
            },
        )


class TestRecommendationsContextSerializer(TestCase):
    """Tests for RecommendationsContextSerializer"""

    def test_successful_serialization(self):
        """Test that context data serializes correctly"""

        serialized_data = RecommendationsContextSerializer(
            {
                "countryCode": "US",
            }
        ).data

        self.assertDictEqual(
            serialized_data,
            {
                "countryCode": "US",
            },
        )

    def test_empty_response_serialization(self):
        """Test that an empty response serializes correctly"""

        serialized_data = RecommendationsContextSerializer(
            {
                "countryCode": "",
            }
        ).data

        self.assertDictEqual(
            serialized_data,
            {
                "countryCode": "",
            },
        )


class TestCrossProductRecommendationsSerializers(TestCase):
    """
    Tests for the CrossProductRecommendationsSerializer,
    AmplitudeRecommendationsSerializer, and CrossProductAndAmplitudeRecommendations Serializer
    """

    def mock_recommended_courses(self, num_of_courses=2):
        """Course data mock"""

        recommended_courses = []

        for index in range(num_of_courses):
            recommended_courses.append(
                {
                    "key": f"edx+HL{index}",
                    "uuid": f"{index}f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
                    "title": f"Title {index}",
                    "image": {
                        "src": f"https://www.logo_image_url{index}.com",
                    },
                    "url_slug": f"https://www.marketing_url{index}.com",
                    "course_type": "executive-education",
                    "owners": [
                        {
                            "key": f"org-{index}",
                            "name": f"org {index}",
                            "logo_image_url": f"https://discovery.com/organization/logos/org-{index}.png",
                        },
                    ],
                    "course_runs": [
                        {
                            "key": f"course-v1:Test+2023_T{index}",
                            "marketing_url": f"https://www.marketing_url{index}.com",
                            "availability": "Current",
                        }
                    ],
                    "active_course_run": {
                        "key": f"course-v1:Test+2023_T{index}",
                        "marketing_url": f"https://www.marketing_url{index}.com",
                        "availability": "Current",
                    },
                    "active_course_run_key": f"course-v1:Test+2023_T{index}",
                    "marketing_url": f"https://www.marketing_url{index}.com",
                    "location_restriction": None
                },
            )

        return recommended_courses

    def test_successful_cross_product_recommendation_serialization(self):
        """Test that course data serializes correctly for CrossProductRecommendationSerializer"""
        courses = self.mock_recommended_courses(num_of_courses=2)

        serialized_data = CrossProductRecommendationsSerializer({
            "courses": courses,
        }).data

        self.assertDictEqual(
            serialized_data,
            mock_cross_product_course_data
        )

    def test_successful_amplitude_recommendations_serialization(self):
        """Test the course data serializes correctly for AmplitudeRecommendationsSerializer"""
        courses = self.mock_recommended_courses(num_of_courses=4)

        serialized_data = AmplitudeRecommendationsSerializer({
            "amplitudeCourses": courses
        }).data

        self.assertDictEqual(
            serialized_data,
            mock_amplitude_course_data
        )

    def test_successful_cross_product_and_amplitude_recommendations_serializer(self):
        """Test that course data serializes correctly for CrossProductAndAmplitudeRecommendationSerializer"""

        cross_product_courses = self.mock_recommended_courses(num_of_courses=2)
        amplitude_courses = self.mock_recommended_courses(num_of_courses=4)

        serialized_data = CrossProductAndAmplitudeRecommendationsSerializer({
            "crossProductCourses": cross_product_courses,
            "amplitudeCourses": amplitude_courses,
        }).data

        self.assertDictEqual(
            serialized_data,
            mock_amplitude_and_cross_product_course_data
        )

    def test_no_cross_product_course_serialization(self):
        """Tests that empty course data for CrossProductRecommendationsSerializer serializes properly"""

        serialized_data = CrossProductRecommendationsSerializer({
            "courses": [],
        }).data

        self.assertDictEqual(
            serialized_data,
            {
                "courses": [],
            },
        )

    def test_no_amplitude_courses_serialization(self):
        """Tests that empty course data for AmplitudeRecommendationsSerializer serializes properly"""

        serialized_data = AmplitudeRecommendationsSerializer({
            "amplitudeCourses": [],
        }).data

        self.assertDictEqual(
            serialized_data,
            {
                "amplitudeCourses": [],
            },
        )

    def test_no_amplitude_and_cross_product_and_course_serialization(self):
        """Tests that empty course data for CrossProductRecommendationsSerializer serializes properly"""

        serialized_data = CrossProductAndAmplitudeRecommendationsSerializer({
            "crossProductCourses": [],
            "amplitudeCourses": []
        }).data

        self.assertDictEqual(
            serialized_data,
            {
                "crossProductCourses": [],
                "amplitudeCourses": []
            },
        )
