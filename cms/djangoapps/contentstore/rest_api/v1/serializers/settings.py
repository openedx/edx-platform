"""
API Serializers for course settings
"""

from rest_framework import serializers

from cms.djangoapps.contentstore.rest_api.serializers.common import CourseCommonSerializer


class CourseSettingsSerializer(serializers.Serializer):
    """Serializer for course settings"""
    about_page_editable = serializers.BooleanField()
    can_show_certificate_available_date_field = serializers.BooleanField()
    course_display_name = serializers.CharField()
    course_display_name_with_default = serializers.CharField()
    credit_eligibility_enabled = serializers.BooleanField()
    credit_requirements = serializers.DictField(required=False)
    enable_extended_course_details = serializers.BooleanField()
    enrollment_end_editable = serializers.BooleanField()
    is_credit_course = serializers.BooleanField()
    is_entrance_exams_enabled = serializers.BooleanField()
    is_prerequisite_courses_enabled = serializers.BooleanField()
    language_options = serializers.ListField(child=serializers.ListField(child=serializers.CharField()))
    lms_link_for_about_page = serializers.URLField()
    licensing_enabled = serializers.BooleanField()
    marketing_enabled = serializers.BooleanField()
    mfe_proctored_exam_settings_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    platform_name = serializers.CharField()
    possible_pre_requisite_courses = CourseCommonSerializer(required=False, many=True)
    short_description_editable = serializers.BooleanField()
    show_min_grade_warning = serializers.BooleanField()
    sidebar_html_enabled = serializers.BooleanField()
    upgrade_deadline = serializers.DateTimeField(allow_null=True)
