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


class CourseProviderSerializer(serializers.Serializer):
    """Info about a course provider (institution/business)"""

    name = serializers.CharField()
    website = serializers.URLField()
    email = serializers.EmailField()


class CourseSerializer(serializers.Serializer):
    """Serializer for course header info"""

    bannerImgSrc = serializers.URLField()
    courseName = serializers.CharField()


class CourseRunSerializer(serializers.Serializer):
    """Serializer for course run info"""

    isPending = serializers.BooleanField()
    isStarted = serializers.BooleanField()
    isFinished = serializers.BooleanField()
    isArchived = serializers.BooleanField()
    courseNumber = serializers.CharField()
    accessExpirationDate = serializers.DateTimeField()
    minPassingGrade = serializers.DecimalField(max_digits=5, decimal_places=2)
    endDate = serializers.DateTimeField()
    homeUrl = serializers.URLField()
    marketingUrl = serializers.URLField()
    progressUrl = serializers.URLField()
    unenrollUrl = serializers.URLField()
    upgradeUrl = serializers.URLField()


class EnrollmentSerializer(serializers.Serializer):
    """Info about this particular enrollment"""

    isAudit = serializers.BooleanField()
    isVerified = serializers.BooleanField()
    canUpgrade = serializers.BooleanField()
    isAuditAccessExpired = serializers.BooleanField()
    isEmailEnabled = serializers.BooleanField()


class GradeDataSerializer(serializers.Serializer):
    """Info about grades for this enrollment"""

    isPassing = serializers.BooleanField()


class LearnerEnrollmentSerializer(serializers.Serializer):
    """Info for displaying an enrollment on the learner dashboard"""

    courseProvider = CourseProviderSerializer(allow_null=True)
    course = CourseSerializer()
    courseRun = CourseRunSerializer()
    enrollment = EnrollmentSerializer()
    gradeData = GradeDataSerializer()

    # certificate,
    # entitlements,
    # programs,


class EntitlementSerializer(serializers.Serializer):
    """Serializer for an unfulfilled entitlement"""


class SuggestedCourseSerializer(serializers.Serializer):
    """Serializer for a suggested course"""


class LearnerDashboardSerializer(serializers.Serializer):
    """Serializer for all info required to render the Learner Dashboard"""

    edx = PlatformSettingsSerializer()
    enrollments = serializers.ListField(
        child=LearnerEnrollmentSerializer(), allow_empty=True
    )
    unfulfilledEntitlements = serializers.ListField(
        child=EntitlementSerializer(), allow_empty=True
    )
    suggestedCourses = serializers.ListField(
        child=SuggestedCourseSerializer(), allow_empty=True
    )
