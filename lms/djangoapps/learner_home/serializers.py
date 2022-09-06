"""
Serializers for the Learner Dashboard
"""
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from common.djangoapps.course_modes.models import CourseMode
from openedx.features.course_experience import course_home_url
from xmodule.data import CertificatesDisplayBehaviors


class PlatformSettingsSerializer(serializers.Serializer):
    """Serializer for platform-level info, emails, and URLs"""

    supportEmail = serializers.EmailField()
    billingEmail = serializers.EmailField()
    courseSearchUrl = serializers.URLField()


class CourseProviderSerializer(serializers.Serializer):
    """Info about a course provider (institution/business)"""

    name = serializers.CharField()


class CourseSerializer(serializers.Serializer):
    """Course header information, derived from a CourseOverview"""

    bannerImgSrc = serializers.URLField(source="banner_image_url")
    courseName = serializers.CharField(source="display_name_with_default")
    courseNumber = serializers.CharField(source="display_number_with_default")


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
    courseId = serializers.CharField(source="course_id")
    minPassingGrade = serializers.DecimalField(
        max_digits=5, decimal_places=2, source="course_overview.lowest_passing_grade"
    )
    startDate = serializers.DateTimeField(source="course_overview.start")
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

    def get_homeUrl(self, instance):
        return course_home_url(instance.course_id)

    def get_progressUrl(self, instance):
        return reverse("progress", kwargs={"course_id": instance.course_id})

    def get_unenrollUrl(self, instance):
        return reverse("course_run_refund_status", args=[instance.course_id])

    def get_upgradeUrl(self, instance):
        """If the enrollment mode has a verified upgrade through ecommerce, return the link"""
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


class HasAccessSerializer(serializers.Serializer):
    """
    Info determining whether a user should be able to view course material.
    Mirrors logic in "show_courseware_links_for" from old dashboard.py
    """

    hasUnmetPrerequisites = serializers.SerializerMethodField()
    isTooEarly = serializers.SerializerMethodField()
    isStaff = serializers.SerializerMethodField()

    def _get_course_access_checks(self, enrollment):
        """Internal helper to unpack access object for this particular enrollment"""
        return self.context.get("course_access_checks", {}).get(
            enrollment.course_id, {}
        )

    def get_hasUnmetPrerequisites(self, enrollment):
        """Whether or not a course has unmet prerequisites"""
        return self._get_course_access_checks(enrollment).get(
            "has_unmet_prerequisites", False
        )

    def get_isTooEarly(self, enrollment):
        """Determine if the course is open to a learner (course has started or user has early beta access)"""
        return self._get_course_access_checks(enrollment).get(
            "is_too_early_to_view", False
        )

    def get_isStaff(self, enrollment):
        """Determine whether a user has staff access to this course"""
        return self._get_course_access_checks(enrollment).get(
            "user_has_staff_access", False
        )


class EnrollmentSerializer(serializers.Serializer):
    """
    Info about this particular enrollment.
    Derived from a CourseEnrollment with added context:
    - "use_ecommerce_payment_flow" (bool): whether or not we use an ecommerce flow to
      upsell.
    - "course_mode_info" (dict): keyed by course ID with the following values:
        - "expiration_datetime" (int): when the verified mode will expire.
        - "show_upsell" (bool): whether or not we offer an upsell for this course.
        - "verified_sku" (uuid): ID for the verified mode for upgrade.
    - "show_courseware_link": keyed by course ID with added metadata.
    - "show_email_settings_for" (dict): keyed by course ID with a boolean whether we
       show email settings.
    """

    accessExpirationDate = serializers.SerializerMethodField()
    isAudit = serializers.SerializerMethodField()
    hasStarted = serializers.SerializerMethodField()
    hasAccess = HasAccessSerializer(source="*")
    isVerified = serializers.SerializerMethodField()
    canUpgrade = serializers.SerializerMethodField()
    isAuditAccessExpired = serializers.SerializerMethodField()
    isEmailEnabled = serializers.SerializerMethodField()
    hasOptedOutOfEmail = serializers.SerializerMethodField()
    lastEnrolled = serializers.DateTimeField(source="created")
    isEnrolled = serializers.BooleanField(source="is_active")

    def get_accessExpirationDate(self, instance):
        return (
            self.context.get("course_mode_info", {})
            .get(instance.course_id)
            .get("expiration_datetime")
        )

    def get_isAudit(self, enrollment):
        return enrollment.mode in CourseMode.AUDIT_MODES

    def get_hasStarted(self, enrollment):
        """Determined based on whether there's a 'resume' link on the course"""
        resume_button_url = self.context.get("resume_course_urls", {}).get(
            enrollment.course_id
        )
        return resume_button_url is not None

    def get_isVerified(self, enrollment):
        return enrollment.is_verified_enrollment()

    def get_canUpgrade(self, enrollment):
        """Determine if a user can upgrade this enrollment to verified track"""
        use_ecommerce_payment_flow = self.context.get(
            "use_ecommerce_payment_flow", False
        )
        course_mode_info = self.context.get("course_mode_info", {}).get(
            enrollment.course_id, {}
        )
        return bool(
            use_ecommerce_payment_flow
            and course_mode_info.get("show_upsell", False)
            and course_mode_info.get("verified_sku", False)
        )

    def get_isAuditAccessExpired(self, enrollment):
        show_courseware_link = self.context.get("show_courseware_link", {}).get(
            enrollment.course.id, {}
        )
        return show_courseware_link.get("error_code") == "audit_expired"

    def get_isEmailEnabled(self, enrollment):
        return enrollment.course_id in self.context.get("show_email_settings_for", [])

    def get_hasOptedOutOfEmail(self, enrollment):
        return enrollment.course_id in self.context.get("course_optouts", [])


class GradeDataSerializer(serializers.Serializer):
    """Info about grades for this enrollment"""

    isPassing = serializers.BooleanField()


class CertificateSerializer(serializers.Serializer):
    """Certificate availability info"""

    availableDate = serializers.SerializerMethodField()
    isRestricted = serializers.SerializerMethodField()
    isEarned = serializers.SerializerMethodField()
    isDownloadable = serializers.SerializerMethodField()
    certPreviewUrl = serializers.SerializerMethodField()

    def get_cert_info(self, enrollment):
        """Utility to grab certificate info for this enrollment or empty object"""
        return self.context.get("cert_statuses", {}).get(enrollment.course.id, {})

    def get_availableDate(self, enrollment):
        """Available date changes based off of Certificate display behavior"""
        course_overview = enrollment.course_overview
        available_date = course_overview.certificate_available_date

        if settings.FEATURES.get("ENABLE_V2_CERT_DISPLAY_SETTINGS", False):
            if (
                course_overview.certificates_display_behavior
                == CertificatesDisplayBehaviors.END_WITH_DATE
                and course_overview.certificate_available_date
            ):
                available_date = course_overview.certificate_available_date
            elif (
                course_overview.certificates_display_behavior
                == CertificatesDisplayBehaviors.END
                and course_overview.end
            ):
                available_date = course_overview.end
        else:
            available_date = course_overview.certificate_available_date

        return serializers.DateTimeField().to_representation(available_date)

    def get_isRestricted(self, enrollment):
        """Cert is considered restricted based on certificate status"""
        return self.get_cert_info(enrollment).get("status") == "restricted"

    def get_isEarned(self, enrollment):
        """Cert is considered earned based on certificate status"""
        is_earned_states = ("downloadable", "certificate_earned_but_not_available")
        return self.get_cert_info(enrollment).get("status") in is_earned_states

    def get_isDownloadable(self, enrollment):
        """Cert is considered downloadable based on certificate status"""
        return self.get_cert_info(enrollment).get("status") == "downloadable"

    def get_certPreviewUrl(self, enrollment):
        """Cert preview URL comes from certificate info"""
        cert_info = self.get_cert_info(enrollment)
        if not cert_info.get("show_cert_web_view", False):
            return None
        else:
            return cert_info.get("cert_web_view_url")


class AvailableEntitlementSessionSerializer(serializers.Serializer):
    """An available entitlement session"""

    startDate = serializers.DateTimeField()
    endDate = serializers.DateTimeField()
    courseId = serializers.CharField()


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

    bannerUrl = serializers.URLField()
    estimatedNumberOfWeeks = serializers.IntegerField()
    logoUrl = serializers.URLField()
    numberOfCourses = serializers.IntegerField()
    programType = serializers.CharField()
    programUrl = serializers.URLField()
    provider = serializers.CharField()
    title = serializers.CharField()


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

    course = CourseSerializer()
    courseRun = CourseRunSerializer(source="*")
    enrollment = EnrollmentSerializer(source="*")
    certificate = CertificateSerializer(source="*")

    # TODO - remove "allow_null" as each of these are implemented, temp for testing.
    courseProvider = CourseProviderSerializer(allow_null=True)
    gradeData = GradeDataSerializer(allow_null=True)
    entitlements = EntitlementSerializer(allow_null=True)
    programs = ProgramsSerializer(allow_null=True)


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

    label = serializers.CharField(source='name')
    url = serializers.SerializerMethodField()

    def get_url(self, instance):
        return urljoin(settings.ENTERPRISE_LEARNER_PORTAL_BASE_URL, instance['uuid'])


class LearnerDashboardSerializer(serializers.Serializer):
    """Serializer for all info required to render the Learner Dashboard"""

    requires_context = True

    emailConfirmation = EmailConfirmationSerializer()
    enterpriseDashboard = EnterpriseDashboardSerializer(allow_null=True)
    platformSettings = PlatformSettingsSerializer()
    courses = serializers.SerializerMethodField()
    suggestedCourses = serializers.ListField(
        child=SuggestedCourseSerializer(), allow_empty=True
    )

    def get_courses(self, instance):
        """
        Get a list of course cards by serializing enrollments and entitlements into
        a single list.
        """
        courses = []

        for enrollment in instance.get("enrollments", []):
            courses.append(
                LearnerEnrollmentSerializer(enrollment, context=self.context).data
            )
        for entitlement in instance.get("unfulfilledEntitlements", []):
            courses.append(
                UnfulfilledEntitlementSerializer(entitlement, context=self.context).data
            )

        return courses
