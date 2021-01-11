# pylint: disable=abstract-method
"""
Dates Tab Serializers. Represents the relevant dates for a Course.
"""


from rest_framework import serializers

from lms.djangoapps.courseware.date_summary import VerificationDeadlineDate
from lms.djangoapps.course_home_api.mixins import DatesBannerSerializerMixin


class DateSummarySerializer(serializers.Serializer):
    """
    Serializer for Date Summary Objects.
    """
    assignment_type = serializers.CharField(default=None)
    complete = serializers.NullBooleanField()
    date = serializers.DateTimeField()
    date_type = serializers.CharField()
    description = serializers.CharField()
    learner_has_access = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    link_text = serializers.CharField()
    title = serializers.CharField()
    extra_info = serializers.CharField()

    def get_learner_has_access(self, block):
        learner_is_full_access = self.context.get('learner_is_full_access', False)
        block_is_verified = (getattr(block, 'contains_gated_content', False) or
                             isinstance(block, VerificationDeadlineDate))
        return (not block_is_verified) or learner_is_full_access

    def get_link(self, block):
        if block.link:
            request = self.context.get('request')
            return request.build_absolute_uri(block.link)
        return ''


class DatesTabSerializer(DatesBannerSerializerMixin, serializers.Serializer):
    """
    Serializer for the Dates Tab
    """
    course_date_blocks = DateSummarySerializer(many=True)
    has_ended = serializers.BooleanField()
    learner_is_full_access = serializers.BooleanField()
    user_timezone = serializers.CharField()
