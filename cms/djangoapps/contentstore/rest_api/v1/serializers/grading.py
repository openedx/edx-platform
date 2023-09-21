"""
API Serializers for course grading
"""

from rest_framework import serializers


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
    course_assignment_lists = serializers.DictField(
        child=serializers.ListSerializer(
            child=serializers.CharField()
        )
    )
    course_details = CourseGradingModelSerializer()
    show_credit_eligibility = serializers.BooleanField()
    is_credit_course = serializers.BooleanField()
