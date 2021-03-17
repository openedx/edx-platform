"""
API Serializers for Contentstore
"""

from rest_framework import serializers

from common.lib.xmodule.xmodule.course_module import get_available_providers


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


class ProctoredExamConfigurationSerializer(serializers.Serializer):
    """ Serializer for various metadata associated with proctored exam settings. """
    proctored_exam_settings = ProctoredExamSettingsSerializer()
    available_proctoring_providers = serializers.ChoiceField(get_available_providers())
    course_start_date = serializers.DateTimeField()
