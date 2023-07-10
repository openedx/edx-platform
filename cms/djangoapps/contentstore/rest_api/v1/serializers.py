"""
API Serializers for Contentstore
"""

from rest_framework import serializers

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
