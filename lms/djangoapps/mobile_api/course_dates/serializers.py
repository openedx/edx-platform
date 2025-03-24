"""
Serializers for course dates.
"""

from crum import get_current_user
from rest_framework import serializers

from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.courses import get_first_component_of_block
from xmodule.modulestore.django import modulestore


class ContentDateSerializer(serializers.Serializer):
    """
    Serializer for ContentDate model with additional fields.
    """

    course_id = serializers.CharField()
    location = serializers.CharField()
    due_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    assignment_title = serializers.SerializerMethodField()
    learner_has_access = serializers.SerializerMethodField()
    course_name = serializers.CharField()
    relative = serializers.BooleanField()
    first_component_block_id = serializers.SerializerMethodField()

    def get_assignment_title(self, obj):
        return modulestore().get_item(obj.location).display_name

    def get_learner_has_access(self, obj):
        block = modulestore().get_item(obj.location)
        return not getattr(block, "contains_gated_content", False)

    def get_first_component_block_id(self, obj):
        user = get_current_user()
        block_data = get_course_blocks(user, obj.location, allow_start_dates_in_future=True, include_completion=True)
        first_block_id = get_first_component_of_block(obj.location, block_data)

        if first_block_id == str(obj.location):
            return None

        return first_block_id
