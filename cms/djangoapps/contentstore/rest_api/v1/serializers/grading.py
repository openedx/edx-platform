"""
API Serializers for course grading
"""

import re

from rest_framework import serializers


class GradersSerializer(serializers.Serializer):
    """ Serializer for graders """
    type = serializers.CharField()
    min_count = serializers.IntegerField()
    drop_count = serializers.IntegerField()
    short_label = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    weight = serializers.IntegerField()
    id = serializers.IntegerField()
    color = serializers.CharField()


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
    course_assignment_lists = serializers.DictField(
        child=serializers.ListSerializer(
            child=serializers.CharField()
        )
    )
    course_details = CourseGradingModelSerializer()
    show_credit_eligibility = serializers.BooleanField()
    is_credit_course = serializers.BooleanField()
    default_grade_designations = serializers.ListSerializer(
        child=serializers.CharField()
    )


class GradingColorSerializer(serializers.Serializer):
    """
    Serializer for grading color
    """
    color = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_color(self, value: str) -> str:
        """
        Validate that the color is a valid hex color code.
        """
        if value and not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
            raise serializers.ValidationError("Invalid color format. Must be a hex color code.")
        return value
