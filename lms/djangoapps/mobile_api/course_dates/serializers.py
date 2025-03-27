"""
Serializers for course dates.
"""

from rest_framework import serializers


class AllCourseDatesSerializer(serializers.Serializer):
    learner_has_access = serializers.SerializerMethodField()
    course_id = serializers.CharField()
    due_date = serializers.DateTimeField(source="date", format="%Y-%m-%dT%H:%M:%S%z")
    assignment_title = serializers.CharField(source="title")
    first_component_block_id = serializers.SerializerMethodField()
    course_name = serializers.CharField(source="course.display_name")
    location = serializers.CharField()
    relative = serializers.BooleanField(source="is_relative")

    def get_learner_has_access(self, block):
        """Whether the learner is blocked (gated) from this content or not"""
        return not getattr(block, "contains_gated_content", False)

    def get_first_component_block_id(self, block):
        return getattr(block, "first_component_block_id", "")
