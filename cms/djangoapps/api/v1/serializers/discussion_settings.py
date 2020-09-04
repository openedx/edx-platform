""" Discussion settings serializers. """


from datetime import datetime

from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import serializers

from models.settings.course_metadata import CourseMetadata
from xmodule.modulestore.django import modulestore


def to_datetime(val, timepart):
    """
    Converts a given string to a datetime object. If the string only
    contains date part, than additional timepart param used to build
    datetime object. Raises ValueError if unable to parse given string.
    """

    parsed_val = parse_datetime(val)
    if not parsed_val:
        parsed_val = parse_date(val)
        if parsed_val:
            parsed_val = datetime.combine(parsed_val, timepart)
        else:
            raise ValueError('Invalid date')
    return parsed_val

def blackout_date_range_validator(value):
    """
    Given two date/datetime string, checks if those are valid dates
    and if 2nd date/datetime is larger than 1st date/datetime. Doesn't
    perform any transformation though, returns ``value`` as is if valid,
    else raises ``serializers.ValidationError``.
    """

    [from_date, to_date] = value
    try:
        from_date = to_datetime(from_date, datetime.min.time())
        to_date = to_datetime(to_date, datetime.max.time())
        if from_date >= to_date:
            raise serializers.ValidationError('Invalid Date Range')
    except Exception:
        raise serializers.ValidationError('Invalid Date')
    return value


class DiscussionSettingsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for discussion related settings. Also overrides ``save`` method
    to support custom update flow of settings
    """

    allow_anonymous_to_peers = serializers.BooleanField()
    allow_anonymous = serializers.BooleanField()
    discussion_blackouts = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField(),
            max_length=2,
            min_length=2,
            validators=(blackout_date_range_validator,)
        ),
    )

    def save(self, **kwargs):
        data_to_save = {key: {'value': val} for key, val in self.validated_data.items()}
        is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
            self.context['course_module'],
            data_to_save,
            user=self.context['user'],
        )
        if not is_valid:
            raise serializers.ValidationError(errors)

        modulestore().update_item(self.context['course_module'], self.context['user'].id)
