"""
Dates Tab Serializers. Represents the relevant dates for a Course.
"""


from rest_framework import serializers

from lms.djangoapps.courseware.date_summary import VerificationDeadlineDate


class DateSummarySerializer(serializers.Serializer):
    """
    Serializer for Date Summary Objects.
    """
    date = serializers.DateTimeField()
    date_type = serializers.CharField()
    description = serializers.CharField()
    learner_has_access = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    title = serializers.CharField()

    def get_learner_has_access(self, block):
        learner_is_verified = self.context.get('learner_is_verified', False)
        block_is_verified = (getattr(block, 'contains_gated_content', False) or
                             isinstance(block, VerificationDeadlineDate))
        return (not block_is_verified) or learner_is_verified

    def get_link(self, block):
        if block.link:
            request = self.context.get('request')
            return request.build_absolute_uri(block.link)
        return ''


class DatesTabSerializer(serializers.Serializer):
    """
    Serializer for the Dates Tab
    """
    course_date_blocks = DateSummarySerializer(many=True)
    display_reset_dates_text = serializers.BooleanField()
    learner_is_verified = serializers.BooleanField()
    user_timezone = serializers.CharField()
    verified_upgrade_link = serializers.URLField()
