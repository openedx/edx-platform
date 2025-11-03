"""
Serializers for Instructor API v2.

These serializers handle data validation and business logic for instructor dashboard endpoints.
Following REST best practices, serializers encapsulate most of the data processing logic.
"""

from django.conf import settings
from django.db.models import Count
from django.utils.html import escape
from django.utils.translation import gettext as _
from edx_when.api import is_enabled_for_course
from rest_framework import serializers

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import (
    CourseFinanceAdminRole,
    CourseInstructorRole,
    CourseSalesAdminRole,
    CourseStaffRole,
)
from lms.djangoapps.bulk_email.api import is_bulk_email_feature_enabled
from lms.djangoapps.bulk_email.models_api import is_bulk_email_disabled_for_course
from lms.djangoapps.certificates.models import (
    CertificateGenerationConfiguration
)
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.courses import get_studio_url
from lms.djangoapps.discussion.django_comment_client.utils import has_forum_access
from lms.djangoapps.instructor import permissions
from lms.djangoapps.instructor.views.instructor_dashboard import show_analytics_dashboard_message, \
    get_analytics_dashboard_message
from openedx.core.djangoapps.discussions.config.waffle_utils import legacy_discussion_experience_enabled
from openedx.core.djangoapps.django_comment_common.models import FORUM_ROLE_ADMINISTRATOR
from xmodule.modulestore.django import modulestore
from ..toggles import data_download_v2_is_enabled


class CourseInformationSerializer(serializers.Serializer):
    """
    Serializer for comprehensive course information.

    This serializer handles the business logic for gathering all course metadata,
    enrollment statistics, permissions, and dashboard configuration.
    """
    course_id = serializers.SerializerMethodField(help_text="Course run key")
    display_name = serializers.SerializerMethodField(help_text="Course display name")
    org = serializers.SerializerMethodField(help_text="Organization identifier")
    course_number = serializers.SerializerMethodField(help_text="Course number")
    enrollment_start = serializers.SerializerMethodField(help_text="Enrollment start date (ISO 8601 with timezone)")
    enrollment_end = serializers.SerializerMethodField(help_text="Enrollment end date (ISO 8601 with timezone)")
    start = serializers.SerializerMethodField(help_text="Course start date (ISO 8601 with timezone)")
    end = serializers.SerializerMethodField(help_text="Course end date (ISO 8601 with timezone)")
    pacing = serializers.SerializerMethodField(help_text="Course pacing type (self or instructor)")
    has_started = serializers.SerializerMethodField(help_text="Whether the course has started based on current time")
    has_ended = serializers.SerializerMethodField(help_text="Whether the course has ended based on current time")
    total_enrollment = serializers.SerializerMethodField(help_text="Total number of enrollments across all modes")
    enrollment_counts = serializers.SerializerMethodField(help_text="Enrollment count breakdown by mode")
    num_sections = serializers.SerializerMethodField(help_text="Number of sections/chapters in the course")
    grade_cutoffs = serializers.SerializerMethodField(help_text="Formatted string of grade cutoffs")
    course_errors = serializers.SerializerMethodField(help_text="List of course validation errors from modulestore")
    studio_url = serializers.SerializerMethodField(help_text="URL to view/edit course in Studio")
    permissions = serializers.SerializerMethodField(help_text="User permissions for instructor dashboard features")
    tabs = serializers.SerializerMethodField(help_text="List of course tabs with configuration and display information")
    disable_buttons = serializers.SerializerMethodField(
        help_text="Whether to disable certain bulk action buttons due to large course size"
    )
    analytics_dashboard_message = serializers.SerializerMethodField(
        help_text="Message about analytics dashboard availability"
    )

    def get_tabs(self, data):
        """Get serialized course tabs."""
        request = data['request']
        course = data['course']
        course_key = course.id

        access = {
            'admin': request.user.is_staff,
            'instructor': bool(has_access(request.user, 'instructor', course)),
            'finance_admin': CourseFinanceAdminRole(course_key).has_user(request.user),
            'sales_admin': CourseSalesAdminRole(course_key).has_user(request.user),
            'staff': bool(has_access(request.user, 'staff', course)),
            'forum_admin': has_forum_access(request.user, course_key, FORUM_ROLE_ADMINISTRATOR),
            'data_researcher': request.user.has_perm(permissions.CAN_RESEARCH, course_key),
        }

        sections = [
            {
                'tab_id': 'course_info',
                'title': _('Course Info'),
                'is_hidden': not access['staff'],
            },
            {
                'tab_id': 'membership',
                'title': _('Membership'),
                'is_hidden': not access['staff'],
            } ,
            {
                'tab_id': 'cohort_management',
                'title': _('Cohorts'),
                'is_hidden': not access['staff'],
            },
            {
                'tab_id': 'student_admin',
                'title': _('Student Admin'),
                'is_hidden': not access['staff'],
            },
            {
                'tab_id': 'discussions_management',
                'title': _('Discussions'),
                'is_hidden': not (access['staff'] and legacy_discussion_experience_enabled(course_key))

            },
            {
                'tab_id': 'data_download_2' if data_download_v2_is_enabled() else 'data_download',
                'title': _('Data Download'),
                'is_hidden': not access['data_researcher'],
            },
            {
                'tab_id': 'instructor_analytics',
                'title': _('Analytics'),
                'is_hidden': not (show_analytics_dashboard_message(course_key)
                                  and (access['staff'] or access['instructor']))

            },
            {
                'tab_id': 'extensions',
                'title': _('Extensions'),
                'is_hidden': not (access['instructor'] and is_enabled_for_course(course_key))
            },
            {
                'tab_id': 'send_email',
                'title': _('Email'),
                'is_hidden': not (is_bulk_email_feature_enabled(course_key) and
                                  (access['staff'] or access['instructor']) and not
                                  is_bulk_email_disabled_for_course(course_key))
            },
            {
                'tab_id': 'open_response_assessment',
                'title': _('Open Responses'),
                'is_hidden': not access['staff'],
            }
        ]

        user_has_access = any([
            request.user.is_staff,
            CourseStaffRole(course_key).has_user(request.user),
            CourseInstructorRole(course_key).has_user(request.user)
        ])
        course_has_special_exams = course.enable_proctored_exams or course.enable_timed_exams
        can_see_special_exams = course_has_special_exams and user_has_access and settings.FEATURES.get(
            'ENABLE_SPECIAL_EXAMS', False)

        sections.append({
            'tab_id': 'special_exams',
            'title': _('Special Exams'),
            'is_hidden': not can_see_special_exams
        })

        # Note: This is hidden for all CCXs
        certs_enabled = CertificateGenerationConfiguration.current().enabled and not hasattr(course_key, 'ccx')
        certs_instructor_enabled = settings.FEATURES.get('ENABLE_CERTIFICATES_INSTRUCTOR_MANAGE', False)
        sections.append({
            'tab_id': 'certificates',
            'title': _('Certificates'),
            'is_hidden': not (certs_enabled and
                              access['admin'] or(access['instructor'] and certs_instructor_enabled))
        })

        return sections

    def get_course_id(self, data):
        """Get course ID as string."""
        return str(data['course'].id)

    def get_display_name(self, data):
        """Get course display name."""
        return data['course'].display_name

    def get_org(self, data):
        """Get organization identifier."""
        return data['course'].id.org

    def get_course_number(self, data):
        """Get course number."""
        return data['course'].id.course

    def get_enrollment_start(self, data):
        """Get enrollment start date."""
        return data['course'].enrollment_start

    def get_enrollment_end(self, data):
        """Get enrollment end date."""
        return data['course'].enrollment_end

    def get_start(self, data):
        """Get course start date."""
        return data['course'].start

    def get_end(self, data):
        """Get course end date."""
        return data['course'].end

    def get_pacing(self, data):
        """Get course pacing type (self or instructor)."""
        return 'self' if data['course'].self_paced else 'instructor'

    def get_has_started(self, data):
        """Check if course has started."""
        return data['course'].has_started()

    def get_has_ended(self, data):
        """Check if course has ended."""
        return data['course'].has_ended()

    def get_total_enrollment(self, data):
        """Get total enrollment count."""
        total_enrollments = CourseEnrollment.objects.filter(
            course_id=data['course'].id,
            is_active=True
        ).count()
        return total_enrollments

    def get_enrollment_counts(self, data):
        """Get enrollment counts by mode."""
        course = data['course']
        total_enrollments = self.get_total_enrollment(data)
        enrollments_by_mode = CourseEnrollment.objects.filter(
            course_id=course.id,
            is_active=True
        ).values('mode').annotate(count=Count('mode'))

        by_mode = {item['mode']: item['count'] for item in enrollments_by_mode}
        by_mode['total'] = total_enrollments

        return by_mode

    def get_num_sections(self, data):
        """Get number of sections in the course."""
        course = data['course']
        return len(course.get_children()) if hasattr(course, 'get_children') else 0

    def get_permissions(self, data):
        """Get user permissions for the course."""
        user = data['user']
        course_key = data['course'].id
        return {
            'admin': user.is_staff,
            'instructor': CourseInstructorRole(course_key).has_user(user),
            'finance_admin': CourseFinanceAdminRole(course_key).has_user(user),
            'sales_admin': CourseSalesAdminRole(course_key).has_user(user),
            'staff': CourseStaffRole(course_key).has_user(user),
            'forum_admin': has_forum_access(user, course_key, FORUM_ROLE_ADMINISTRATOR),
            'data_researcher': user.has_perm(permissions.CAN_RESEARCH, course_key),
        }

    def get_grade_cutoffs(self, data):
        """
        Format grade cutoffs as a human-readable string.

        Args:
            data: Dictionary containing course object

        Returns:
            str: Formatted grade cutoffs (e.g., "A is 0.9, B is 0.8, C is 0.7")
        """
        course = data['course']
        if not hasattr(course, 'grading_policy') or not course.grading_policy:
            return ""

        grading_policy = course.grading_policy
        if 'GRADER' not in grading_policy:
            return ""

        grade_cutoffs = grading_policy.get('GRADE_CUTOFFS', {})
        if not grade_cutoffs:
            return ""

        # Sort by cutoff value descending
        sorted_cutoffs = sorted(grade_cutoffs.items(), key=lambda x: x[1], reverse=True)

        # Format as "A is 0.9, B is 0.8, ..."
        formatted = ", ".join([f"{grade} is {cutoff}" for grade, cutoff in sorted_cutoffs])
        return formatted

    def get_course_errors(self, data):
        """Get course validation errors from modulestore."""
        course = data['course']
        try:
            errors = modulestore().get_course_errors(course.id)
            course_errors = [(escape(str(error)), '') for (error, _) in errors]
        except (AttributeError, KeyError):
            course_errors = []
        return course_errors

    def get_studio_url(self, data):
        """Get Studio URL for the course."""
        return get_studio_url(data['course'], 'course')

    def get_disable_buttons(self, data):
        """Check if buttons should be disabled for large courses."""
        return not CourseEnrollment.objects.is_small_course(data['course'].id)

    def get_analytics_dashboard_message(self, data):
        """Get analytics dashboard availability message."""
        return get_analytics_dashboard_message(data['course'].id)


class InstructorTaskSerializer(serializers.Serializer):
    """Serializer for instructor task details."""
    task_id = serializers.UUIDField()
    task_type = serializers.CharField()
    task_state = serializers.ChoiceField(choices=["PENDING", "PROGRESS", "SUCCESS", "FAILURE", "REVOKED"])
    status = serializers.CharField()
    created = serializers.DateTimeField()
    duration_sec = serializers.CharField()
    task_message = serializers.CharField()
    requester = serializers.CharField()
    task_input = serializers.CharField()
    task_output = serializers.CharField(allow_null=True)


class InstructorTaskListSerializer(serializers.Serializer):
    tasks = InstructorTaskSerializer(many=True)
