"""
API Serializers for Contentstore
"""

from rest_framework import serializers

from openedx.core.lib.api.serializers import CourseKeyField
from xmodule.course_block import get_available_providers


class ProctoredExamSettingsSerializer(serializers.Serializer):
    """ Serializer for edX Staff proctored exam settings. """
    enable_proctored_exams = serializers.BooleanField()
    allow_proctoring_opt_out = serializers.BooleanField()
    proctoring_provider = serializers.CharField()
    proctoring_escalation_email = serializers.CharField(required=False, allow_null=True)
    create_zendesk_tickets = serializers.BooleanField()


class LimitedProctoredExamSettingsSerializer(serializers.Serializer):
    """Serializer for non edX Staff for proctored exam settings"""
    enable_proctored_exams = serializers.BooleanField()
    proctoring_provider = serializers.CharField()
    proctoring_escalation_email = serializers.CharField(allow_blank=True)
    create_zendesk_tickets = serializers.BooleanField()


class ProctoredExamConfigurationSerializer(serializers.Serializer):
    """ Serializer for various metadata associated with proctored exam settings. """
    proctored_exam_settings = ProctoredExamSettingsSerializer()
    available_proctoring_providers = serializers.ChoiceField(get_available_providers())
    course_start_date = serializers.DateTimeField()


class GradersSerializer(serializers.Serializer):
    """ Serializer for graders """
    type = serializers.CharField()
    min_count = serializers.IntegerField()
    drop_count = serializers.IntegerField()
    short_label = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    weight = serializers.IntegerField()
    id = serializers.IntegerField()


class GracePeriodSerializer(serializers.Serializer):
    """ Serializer for course grace period """
    hours = serializers.IntegerField()
    minutes = serializers.IntegerField()


class CourseGradingModelSerializer(serializers.Serializer):
    """ Serializer for course grading model data """
    graders = GradersSerializer(many=True)
    grade_cutoffs = serializers.DictField(child=serializers.FloatField())
    grace_period = GracePeriodSerializer(required=False, allow_null=True)
    minimum_grade_credit = serializers.FloatField()


class CourseGradingSerializer(serializers.Serializer):
    """ Serializer for course grading context data """
    mfe_proctored_exam_settings_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    course_details = CourseGradingModelSerializer()
    show_credit_eligibility = serializers.BooleanField()
    is_credit_course = serializers.BooleanField()
    default_grade_designations = serializers.ListSerializer(
        child=serializers.CharField()
    )


class InstructorInfoSerializer(serializers.Serializer):
    """ Serializer for instructor info """
    name = serializers.CharField(allow_blank=True)
    title = serializers.CharField(allow_blank=True)
    organization = serializers.CharField(allow_blank=True)
    image = serializers.CharField(allow_blank=True)
    bio = serializers.CharField(allow_blank=True)


class InstructorsSerializer(serializers.Serializer):
    """ Serializer for instructors """
    instructors = InstructorInfoSerializer(many=True, allow_empty=True)


class CourseDetailsSerializer(serializers.Serializer):
    """ Serializer for course details """
    about_sidebar_html = serializers.CharField(allow_null=True, allow_blank=True)
    banner_image_name = serializers.CharField(allow_blank=True)
    banner_image_asset_path = serializers.CharField()
    certificate_available_date = serializers.DateTimeField()
    certificates_display_behavior = serializers.CharField(allow_null=True)
    course_id = serializers.CharField()
    course_image_asset_path = serializers.CharField(allow_blank=True)
    course_image_name = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    duration = serializers.CharField(allow_blank=True)
    effort = serializers.CharField(allow_null=True, allow_blank=True)
    end_date = serializers.DateTimeField(allow_null=True)
    enrollment_end = serializers.DateTimeField(allow_null=True)
    enrollment_start = serializers.DateTimeField(allow_null=True)
    entrance_exam_enabled = serializers.CharField(allow_blank=True)
    entrance_exam_id = serializers.CharField(allow_blank=True)
    entrance_exam_minimum_score_pct = serializers.CharField(allow_blank=True)
    instructor_info = InstructorsSerializer()
    intro_video = serializers.CharField(allow_null=True)
    language = serializers.CharField(allow_null=True)
    learning_info = serializers.ListField(child=serializers.CharField(allow_blank=True))
    license = serializers.CharField(allow_null=True)
    org = serializers.CharField()
    overview = serializers.CharField(allow_blank=True)
    pre_requisite_courses = serializers.ListField(child=CourseKeyField())
    run = serializers.CharField()
    self_paced = serializers.BooleanField()
    short_description = serializers.CharField(allow_blank=True)
    start_date = serializers.DateTimeField()
    subtitle = serializers.CharField(allow_blank=True)
    syllabus = serializers.CharField(allow_null=True)
    title = serializers.CharField(allow_blank=True)
    video_thumbnail_image_asset_path = serializers.CharField()
    video_thumbnail_image_name = serializers.CharField(allow_blank=True)


class PossiblePreRequisiteCourseSerializer(serializers.Serializer):
    """ Serializer for possible pre requisite course """
    course_key = CourseKeyField()
    display_name = serializers.CharField()
    lms_link = serializers.CharField()
    number = serializers.CharField()
    org = serializers.CharField()
    rerun_link = serializers.CharField()
    run = serializers.CharField()
    url = serializers.CharField()


class CourseSettingsSerializer(serializers.Serializer):
    """ Serializer for course settings """
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
    marketing_enabled = serializers.BooleanField()
    mfe_proctored_exam_settings_url = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    possible_pre_requisite_courses = PossiblePreRequisiteCourseSerializer(required=False, many=True)
    short_description_editable = serializers.BooleanField()
    show_min_grade_warning = serializers.BooleanField()
    sidebar_html_enabled = serializers.BooleanField()
    upgrade_deadline = serializers.DateTimeField(allow_null=True)
    use_v2_cert_display_settings = serializers.BooleanField()
