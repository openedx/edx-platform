"""Tests for serializers for the Learner Recommendations"""

from uuid import uuid4

from django.test import TestCase

from lms.djangoapps.learner_recommendations.serializers import (
    DashboardRecommendationsSerializer,
    CrossProductRecommendationsSerializer
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


class TestCrossProductRecommendationsSerializer(TestCase):
    """Tests for the Cross Product Recommendations Serializer"""

    def mock_recommended_courses(self, num_of_courses):
        """Course data mock"""

        recommended_courses = []

        for i in range(num_of_courses):
            recommended_courses.append(
                {
                    "key": f"edx+HL{i}",
                    "uuid": f"{i}f8cb2c9-589b-4d1e-88c1-b01a02db3a9c",
                    "title": f"Title {i}",
                    "image": {
                        "src": f"https://www.logo_image_url{i}.com",
                    },
                    "url_slug": f"https://www.marketing_url{i}.com",
                    "course_type": "executive-education",
                    "owners": [
                        {
                            "key": f"org-{i}",
                            "name": f"org {i}",
                            "logo_image_url": f"https://discovery.com/organization/logos/org-{i}.png",
                        },
                    ],
                    "course_runs": [
                        {
                            "key": "course-v1:Test+2023_T2",
                            "marketing_url": "https://www.marketing_url.com",
                            "availability": "Current",
                        }
                    ],
                    "active_course_run": {
                        "key": "course-v1:Test+2023_T2",
                        "marketing_url": "https://www.marketing_url.com",
                        "availability": "Current",
                    },
                    "location_restriction": None
                },
            )

        return recommended_courses

    def test_successful_serialization(self):
        courses = self.mock_recommended_courses(num_of_courses=2)

        serialized_data = CrossProductRecommendationsSerializer({
            "courses": courses
        }).data

        self.assertDictEqual(
            serialized_data,
            {
                "courses": [
                    {
                        "key": serialized_data["courses"][0]["key"],
                        "uuid": serialized_data["courses"][0]["uuid"],
                        "title": serialized_data["courses"][0]["title"],
                        "image": {
                            "src": serialized_data["courses"][0]["image"]["src"],
                        },
                        "prospectusPath": serialized_data["courses"][0]["prospectusPath"],
                        "owners": [{
                            "key": serialized_data["courses"][0]["owners"][0]["key"],
                            "name": serialized_data["courses"][0]["owners"][0]["name"],
                            "logoImageUrl": serialized_data["courses"][0]["owners"][0]["logoImageUrl"]
                        }],
                        "activeCourseRun": {
                            "key": serialized_data["courses"][0]["activeCourseRun"]["key"],
                            "marketingUrl": serialized_data["courses"][0]["activeCourseRun"]["marketingUrl"],
                        },
                        "courseType": serialized_data["courses"][0]["courseType"]
                    },
                    {
                        "key": serialized_data["courses"][1]["key"],
                        "uuid": serialized_data["courses"][1]["uuid"],
                        "title": serialized_data["courses"][1]["title"],
                        "image": {
                            "src": serialized_data["courses"][1]["image"]["src"],
                        },
                        "prospectusPath": serialized_data["courses"][1]["prospectusPath"],
                        "owners": [{
                            "key": serialized_data["courses"][1]["owners"][0]["key"],
                            "name": serialized_data["courses"][1]["owners"][0]["name"],
                            "logoImageUrl": serialized_data["courses"][1]["owners"][0]["logoImageUrl"]
                        }],
                        "activeCourseRun": {
                            "key": serialized_data["courses"][1]["activeCourseRun"]["key"],
                            "marketingUrl": serialized_data["courses"][1]["activeCourseRun"]["marketingUrl"],
                        },
                        "courseType": serialized_data["courses"][1]["courseType"],
                    },
                ],
            },
        )

    def test_no_course_data_serialization(self):
        courses = self.mock_recommended_courses(num_of_courses=0)

        serialized_data = CrossProductRecommendationsSerializer({
            "courses": courses
        }).data

        self.assertDictEqual(
            serialized_data,
            {
                "courses": []
            },
        )
