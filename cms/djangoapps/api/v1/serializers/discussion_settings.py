""" Discussion settings serializers. """


from rest_framework import serializers

from models.settings.course_metadata import CourseMetadata
from common.lib.xmodule.xmodule.course_module import validate_blackout_datetimes


def blackout_date_range_validator(blackout_dates):
    """
    Given two datetime object, checks if 2nd date/datetime is larger than
    1st date/datetime. returns ``value`` as is if valid,
    else raises ``serializers.ValidationError``.
    """
    try:
        return validate_blackout_datetimes(blackout_dates)
    except (TypeError, ValueError):
        raise serializers.ValidationError("Invalid blackout dates")


class DiscussionSettingsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for discussion related settings. Also overrides ``save`` method
    to support custom update flow of settings
    """

    allow_anonymous_to_peers = serializers.BooleanField()
    allow_anonymous = serializers.BooleanField()
    discussion_blackouts = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField()
        ),
        validators=(blackout_date_range_validator,)
    )

    def save(self, **kwargs):
        data_to_save = {key: {'value': val} for key, val in self.validated_data.items()}
        CourseMetadata.update_from_json(
            self.context['course_module'],
            data_to_save,
            user=self.context['user'],
        )
