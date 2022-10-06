# pylint: disable=abstract-method
"""
Dates Tab Serializers. Represents the relevant dates for a Course.
"""


from rest_framework import serializers

from lms.djangoapps.course_home_api.serializers import DatesBannerSerializer
from lms.djangoapps.courseware.date_summary import VerificationDeadlineDate


class DateSummarySerializer(serializers.Serializer):
    """
    Serializer for Date Summary Objects.
    """
    assignment_type = serializers.CharField(default=None)
    complete = serializers.BooleanField(allow_null=True)
    date = serializers.DateTimeField()
    date_type = serializers.CharField()
    description = serializers.CharField()
    learner_has_access = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    link_text = serializers.CharField()
    title = serializers.CharField()
    extra_info = serializers.CharField()
    first_component_block_id = serializers.SerializerMethodField()

    def get_learner_has_access(self, block):
        """Whether the learner is blocked (gated) from this content or not"""
        if isinstance(block, VerificationDeadlineDate):
            # This date block isn't an assignment, so doesn't have contains_gated_content set for it
            return self.context.get('learner_is_full_access', False)

        return not getattr(block, 'contains_gated_content', False)

    def get_link(self, block):
        if block.link:
            return block.link
        return ''

    def get_first_component_block_id(self, block):
        return getattr(block, 'first_component_block_id', '')


class DatesTabSerializer(DatesBannerSerializer):
    """
    Serializer for the Dates Tab
    """
    course_date_blocks = DateSummarySerializer(many=True)
    has_ended = serializers.BooleanField()
    learner_is_full_access = serializers.BooleanField()
    user_timezone = serializers.CharField()
