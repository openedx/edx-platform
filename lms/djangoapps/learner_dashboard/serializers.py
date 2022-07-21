"""
Serializers for the Learner Dashboard
"""

from django.urls import reverse
from openedx.features.course_experience import course_home_url
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
    """Course header information, derived from a CourseOverview"""

    bannerImgSrc = serializers.URLField(source="banner_image_url")
    courseName = serializers.CharField(source="display_name_with_default")


class CourseRunSerializer(serializers.Serializer):
    """
    Information about a course run.
    Derived from the CourseEnrollment with required context:
    - "resume_course_urls" (dict) with a matching course_id key
    - "ecommerce_payment_page" (url) root to the ecommerce page
    - "course_mode_info" (dict) keyed by course ID, with sub info:
        - "verified_sku" (uid, optional) if the course has an upgrade identifier
        - "days_for_upsell" (int, optional) days before audit student loses access
    """

    requires_context = True

    isStarted = serializers.SerializerMethodField()
    isArchived = serializers.SerializerMethodField()
    courseNumber = serializers.CharField(
        source="course_overview.display_number_with_default"
    )
    accessExpirationDate = serializers.SerializerMethodField()
    minPassingGrade = serializers.DecimalField(
        max_digits=5, decimal_places=2, source="course_overview.lowest_passing_grade"
    )
    endDate = serializers.DateTimeField(source="course_overview.end")
    homeUrl = serializers.SerializerMethodField()
    marketingUrl = serializers.URLField(
        source="course_overview.marketing_url", allow_null=True
    )
    progressUrl = serializers.SerializerMethodField()
    unenrollUrl = serializers.SerializerMethodField()
    upgradeUrl = serializers.SerializerMethodField()
    resumeUrl = serializers.SerializerMethodField()

    def get_isStarted(self, instance):
        return instance.course_overview.has_started()

    def get_isArchived(self, instance):
        return instance.course_overview.has_ended()

    def get_accessExpirationDate(self, instance):
        return (
            self.context.get("course_mode_info", {})
            .get(instance.course_id)
            .get("days_for_upsell")
        )

    def get_homeUrl(self, instance):
        return course_home_url(instance.course_id)

    def get_progressUrl(self, instance):
        return reverse("progress", kwargs={"course_id": instance.course_id})

    def get_unenrollUrl(self, instance):
        return reverse("course_run_refund_status", args=[instance.course_id])

    def get_upgradeUrl(self, instance):
        ecommerce_payment_page = self.context.get("ecommerce_payment_page")
        verified_sku = (
            self.context.get("course_mode_info", {})
            .get(instance.course_id, {})
            .get("verified_sku")
        )

        if ecommerce_payment_page and verified_sku:
            return f"{ecommerce_payment_page}?sku={verified_sku}"

    def get_resumeUrl(self, instance):
        return self.context.get("resume_course_urls", {}).get(instance.course_id)


class EnrollmentSerializer(serializers.Serializer):
    """Info about this particular enrollment"""

    isAudit = serializers.BooleanField()
    isVerified = serializers.BooleanField()
    canUpgrade = serializers.BooleanField()
    isAuditAccessExpired = serializers.BooleanField()
    isEmailEnabled = serializers.BooleanField()
    lastEnrolled = serializers.DateTimeField()
    isEnrolled = serializers.BooleanField()


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
    expirationDate = serializers.DateTimeField()


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
    """
    Info for displaying an enrollment on the learner dashboard.
    Derived from a CourseEnrollment with added context.
    """

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


class EmailConfirmationSerializer(serializers.Serializer):
    """Serializer for email confirmation banner resources"""

    isNeeded = serializers.BooleanField()
    sendEmailUrl = serializers.URLField()


class EnterpriseDashboardSerializer(serializers.Serializer):
    """Serializer for individual enterprise dashboard data"""

    label = serializers.CharField()
    url = serializers.URLField()


class EnterpriseDashboardsSerializer(serializers.Serializer):
    """Listing of available enterprise dashboards"""

    availableDashboards = serializers.ListField(
        child=EnterpriseDashboardSerializer(), allow_empty=True
    )
    mostRecentDashboard = EnterpriseDashboardSerializer()


class LearnerDashboardSerializer(serializers.Serializer):
    """Serializer for all info required to render the Learner Dashboard"""

    requires_context = True

    emailConfirmation = EmailConfirmationSerializer()
    enterpriseDashboards = EnterpriseDashboardsSerializer()
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
