"""Tests for serializers for the Learner Home"""

from uuid import uuid4

from django.test import TestCase

from lms.djangoapps.learner_home.recommendations.serializers import (
    CourseRecommendationSerializer,
)
from lms.djangoapps.learner_home.test_utils import (
    random_url,
)


class TestCourseRecommendationSerializer(TestCase):
    """High-level tests for CourseRecommendationSerializer"""

    @classmethod
    def mock_recommended_courses(cls, courses_count=2):
        """Sample course data"""

        recommended_courses = []

        for _ in range(courses_count):
            recommended_courses.append(
                {
                    "course_key": str(uuid4()),
                    "logo_image_url": random_url(),
                    "marketing_url": random_url(),
                    "title": str(uuid4()),
                },
            )

        return recommended_courses

    def test_no_recommended_courses(self):
        """That that data serializes correctly for empty courses list"""

        recommended_courses = self.mock_recommended_courses(courses_count=0)

        output_data = CourseRecommendationSerializer(
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

        output_data = CourseRecommendationSerializer(
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
