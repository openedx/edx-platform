"""
Serializers for the mobile notifications API.
"""
from rest_framework import serializers

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference
)
from ..base_notification import COURSE_NOTIFICATION_APPS, COURSE_NOTIFICATION_TYPES
from ..utils import remove_preferences_with_no_access


def add_info_to_notification_config(config_obj):
    """
    Add info of all notification types
    """

    config = config_obj['notification_preference_config']
    for notification_app, app_prefs in config.items():
        notification_types = app_prefs.get('notification_types', {})
        for notification_type, type_prefs in notification_types.items():
            if notification_type == "core":
                type_info = COURSE_NOTIFICATION_APPS.get(notification_app, {}).get('core_info', '')
            else:
                type_info = COURSE_NOTIFICATION_TYPES.get(notification_type, {}).get('info', '')
            type_prefs['info'] = type_info
    return config_obj


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user notification preferences.
    """
    course_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CourseNotificationPreference
        fields = ('id', 'course_name', 'course_id', 'notification_preference_config',)
        read_only_fields = ('id', 'course_name', 'course_id',)
        write_only_fields = ('notification_preference_config',)

    def to_representation(self, instance):
        """
        Override to_representation to add info of all notification types
        """
        preferences = super().to_representation(instance)
        user = self.context['user']
        preferences = add_info_to_notification_config(preferences)
        preferences = remove_preferences_with_no_access(preferences, user)
        return preferences

    def get_course_name(self, obj):
        """
        Returns course name from course id.
        """
        return CourseOverview.get_from_id(obj.course_id).display_name
