"""
Serializers for course dates.
"""

from rest_framework import serializers

from xmodule.modulestore.django import modulestore


class ContentDateSerializer(serializers.Serializer):
    """
    Serializer for ContentDate model with additional fields.
    """

    course_id = serializers.CharField()
    assignment_block_id = serializers.CharField(source="location")
    due_date = serializers.CharField()
    assignment_title = serializers.SerializerMethodField()
    learner_has_access = serializers.SerializerMethodField()
    course_name = serializers.CharField()

    def get_assignment_title(self, obj):
        return modulestore().get_item(obj.location).display_name

    def get_learner_has_access(self, obj):
        block = modulestore().get_item(obj.location)
        return not getattr(block, "contains_gated_content", False)
