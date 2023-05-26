"""
Serializers for the notifications API.
"""
from rest_framework import serializers

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.notifications.models import Notification, NotificationPreference


class CourseOverviewSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseOverview model.
    """

    class Meta:
        model = CourseOverview
        fields = ('id', 'display_name')


class NotificationCourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for CourseEnrollment model.
    """
    course = CourseOverviewSerializer()

    class Meta:
        model = CourseEnrollment
        fields = ('course', 'is_active', 'mode')


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for user notification preferences.
    """
    course_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = NotificationPreference
        fields = ('id', 'course_name', 'course_id', 'notification_preference_config',)
        read_only_fields = ('id', 'course_name', 'course_id',)
        write_only_fields = ('notification_preference_config',)

    def get_course_name(self, obj):
        """
        Returns course name from course id.
        """
        return CourseOverview.get_from_id(obj.course_id).display_name

    def update(self, instance, validated_data):
        for key, val in validated_data.items():
            setattr(instance, key, val)
        instance.save()
        return instance


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Notification model.
    """

    class Meta:
        model = Notification
        fields = (
            'id',
            'app_name',
            'notification_type',
            'content',
            'content_context',
            'content_url',
            'last_read',
            'last_seen',
        )
