"""
Serializers for the Learner Dashboard
"""

from rest_framework import serializers


class PlatformSettingsSerializer(serializers.Serializer):
    """Serializer for platform-level info, emails, and URLs"""

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


class CertificateSerializer(serializers.Serializer):
    """Certificate availability info"""

    availableDate = serializers.DateTimeField(allow_null=True)
    isRestricted = serializers.BooleanField()
    isAvailable = serializers.BooleanField()
    isEarned = serializers.BooleanField()
    isDownloadable = serializers.BooleanField()
    certPreviewUrl = serializers.URLField(allow_null=True)
    certDownloadUrl = serializers.URLField(allow_null=True)
    honorCertDownloadUrl = serializers.URLField(allow_null=True)


class AvailableEntitlementSessionSerializer(serializers.Serializer):
    """An available entitlement session"""

    startDate = serializers.DateTimeField()
    endDate = serializers.DateTimeField()
    courseNumber = serializers.CharField()


class EntitlementSerializer(serializers.Serializer):
    """Entitlements info"""

    availableSessions = serializers.ListField(
        child=AvailableEntitlementSessionSerializer(), allow_empty=True
    )
    isRefundable = serializers.BooleanField()
    isFulfilled = serializers.BooleanField()
    canViewCourse = serializers.BooleanField()
    changeDeadline = serializers.DateTimeField()
    isExpired = serializers.BooleanField()


class RelatedProgramSerializer(serializers.Serializer):
    """Related programs information"""

    provider = serializers.CharField()
    programUrl = serializers.URLField()
    bannerUrl = serializers.URLField()
    logoUrl = serializers.URLField()
    title = serializers.CharField()
    # Note - this should probably be a choice, eventually
    programType = serializers.CharField()
    programTypeUrl = serializers.URLField()
    numberOfCourses = serializers.IntegerField()
    estimatedNumberOfWeeks = serializers.IntegerField()


class ProgramsSerializer(serializers.Serializer):
    """Programs information"""

    relatedPrograms = serializers.ListField(
        child=RelatedProgramSerializer(), allow_empty=True
    )


class LearnerEnrollmentSerializer(serializers.Serializer):
    """Info for displaying an enrollment on the learner dashboard"""

    courseProvider = CourseProviderSerializer(allow_null=True)
    course = CourseSerializer()
    courseRun = CourseRunSerializer()
    enrollment = EnrollmentSerializer()
    gradeData = GradeDataSerializer()
    certificate = CertificateSerializer()
    entitlements = EntitlementSerializer()
    programs = ProgramsSerializer()


class UnfulfilledEntitlementSerializer(serializers.Serializer):
    """Serializer for an unfulfilled entitlement"""

    courseProvider = CourseProviderSerializer(allow_null=True)
    course = CourseSerializer()
    entitlements = EntitlementSerializer()
    programs = ProgramsSerializer()


class SuggestedCourseSerializer(serializers.Serializer):
    """Serializer for a suggested course"""

    bannerUrl = serializers.URLField()
    logoUrl = serializers.URLField()
    title = serializers.CharField()
    courseUrl = serializers.URLField()


class LearnerDashboardSerializer(serializers.Serializer):
    """Serializer for all info required to render the Learner Dashboard"""

    platformSettings = PlatformSettingsSerializer()
    enrollments = serializers.ListField(
        child=LearnerEnrollmentSerializer(), allow_empty=True
    )
    unfulfilledEntitlements = serializers.ListField(
        child=UnfulfilledEntitlementSerializer(), allow_empty=True
    )
    suggestedCourses = serializers.ListField(
        child=SuggestedCourseSerializer(), allow_empty=True
    )
