"""
Serializers for course dates.
"""
from rest_framework import serializers


class AllCourseDatesSerializer(serializers.Serializer):
    learner_has_access = serializers.SerializerMethodField()
    course_id = serializers.CharField(source="content_date.course_id")
    due_date = serializers.DateTimeField(source="actual_date", format="%Y-%m-%dT%H:%M:%S%z")
    assignment_title = serializers.CharField(source="content_date.assignment_title")
    first_component_block_id = serializers.CharField()
    course_name = serializers.CharField(source="content_date.course_name")
    location = serializers.CharField()
    relative = serializers.SerializerMethodField()

    def get_learner_has_access(self, block):
        """Whether the learner is blocked (gated) from this content or not"""
        # todo: needs implementing
        return not getattr(block, "contains_gated_content", False)

    def get_relative(self, obj):
        return bool(obj.rel_date)
