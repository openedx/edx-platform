"""
Serializers for course dates.
"""
from rest_framework import serializers


class AllCourseDatesSerializer(serializers.Serializer):
    learner_has_access = serializers.BooleanField()
    course_id = serializers.CharField(source="content_date.course_id")
    due_date = serializers.DateTimeField(source="actual_date", format="%Y-%m-%dT%H:%M:%S%z")
    assignment_title = serializers.CharField(source="content_date.assignment_title")
    first_component_block_id = serializers.CharField()
    course_name = serializers.CharField(source="content_date.course_name")
    location = serializers.CharField()
    relative = serializers.SerializerMethodField()

    @staticmethod
    def get_relative(obj):
        return obj.rel_date is not None
