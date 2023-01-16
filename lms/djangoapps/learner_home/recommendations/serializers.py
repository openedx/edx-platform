"""
Serializers for Course Recommendations
"""
from rest_framework import serializers


class RecommendedCourseSerializer(serializers.Serializer):
    """Serializer for a recommended course from the recommendation engine"""

    courseKey = serializers.CharField(source="course_key")
    logoImageUrl = serializers.URLField(source="logo_image_url")
    marketingUrl = serializers.URLField(source="marketing_url")
    title = serializers.CharField()


class CourseRecommendationSerializer(serializers.Serializer):
    """Recommended courses by the Amplitude"""

    courses = serializers.ListField(
        child=RecommendedCourseSerializer(), allow_empty=True
    )
    isControl = serializers.BooleanField(
        source="is_control",
        default=None
    )
