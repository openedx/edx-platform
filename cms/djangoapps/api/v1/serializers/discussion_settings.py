""" Discussion settings serializers. """


from rest_framework import serializers

from models.settings.course_metadata import CourseMetadata
from xmodule.modulestore.django import modulestore


def get_settings_serializer(value_field_cls):
    """Creates & returns a settings serializer class dynamicly."""

    class SettingSerializer(serializers.Serializer):

        help = serializers.CharField(read_only=True)
        hide_on_enabled_publisher = serializers.BooleanField(read_only=True)
        display_name = serializers.CharField(read_only=True)
        deprecated = serializers.BooleanField(read_only=True)
        value = value_field_cls

    return SettingSerializer()


blackout_date_range_field = serializers.ListField(
    child=serializers.ListField(
        child=serializers.CharField(),
        max_length=2,
        min_length=2
    )
)


class DiscussionSettingsSerializer(serializers.Serializer):

    discussion_sort_alpha = get_settings_serializer(
        value_field_cls=serializers.BooleanField()
    )

    discussion_link = get_settings_serializer(
        value_field_cls=serializers.URLField(allow_null=True)
    )

    allow_anonymous_to_peers = get_settings_serializer(
        value_field_cls=serializers.BooleanField()
    )

    allow_anonymous = get_settings_serializer(
        value_field_cls=serializers.BooleanField()
    )

    discussion_blackouts = get_settings_serializer(
        value_field_cls=blackout_date_range_field
    )

    def validate(self, data):
        is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
            self.context['course_module'],
            data,
            user=self.context['user'],
        )
        if not is_valid:
            raise serializers.ValidationError(errors)
        else:
            return updated_data

    def save(self):
        with modulestore().bulk_operations(self.context['course_key']):
            modulestore().update_item(self.context['course_module'], self.context['user'].id)
