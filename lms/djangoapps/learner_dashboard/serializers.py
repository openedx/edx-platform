"""
Serializers for the Learner Dashboard
"""

from rest_framework import serializers


class PlatformSettingsSerializer(serializers.Serializer):
    """Serializer for edX platform-level info, emails, and URLs"""

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

    edx = PlatformSettingsSerializer()
    enrollments = serializers.ListField(child=EnrollmentSerializer(), allow_empty=True)
    unfulfilledEntitlements = serializers.ListField(child=EntitlementSerializer(), allow_empty=True)
    suggestedCourses = serializers.ListField(child=SuggestedCourseSerializer(), allow_empty=True)
