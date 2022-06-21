"""
Serializers for the Learner Dashboard
"""

from rest_framework import serializers


class EdxSerializer(serializers.Serializer):
    """Serializer for edX-related emails and URLs"""

    feedbackEmail = serializers.EmailField()
    supportEmail = serializers.EmailField()
    billingEmail = serializers.EmailField()
    courseSearchUrl = serializers.URLField()


class EnrollmentSerializer(serializers.Serializer):
    """Serializer for an enrollment"""


class EntitlementSerializer(serializers.Serializer):
    """Serializer for an unfulfilled entitlement"""


class SuggestedCourseSerializer(serializers.Serializer):
    """Serializer for a suggested course"""


class LearnerDashboardSerializer(serializers.Serializer):
    """Serializer for all info required to render the Learner Dashboard"""

    edx = EdxSerializer()
    enrollments = serializers.ListField(child=EnrollmentSerializer())
    unfulfilledEntitlements = serializers.ListField(child=EntitlementSerializer())
    suggestedCourses = serializers.ListField(child=SuggestedCourseSerializer())
