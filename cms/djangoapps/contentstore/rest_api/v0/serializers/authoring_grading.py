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

    class Meta:
        ref_name = "authoring_grading.Graders.v0"


class CourseGradingModelSerializer(serializers.Serializer):
    """ Serializer for course grading model data """
    graders = GradersSerializer(many=True, allow_null=True, allow_empty=True)

    class Meta:
        ref_name = "authoring_grading.CourseGrading.v0"
