"""
Serializers (Django REST Framework) for Data Objects
"""

from rest_framework import serializers

from edx_notifications.base_data import (
    DictField
)


class DictFieldSerializer(serializers.Field):
    """
    A specialized serializer for a dictionary field
    """

    def to_representation(self, obj):
        """
        to json format
        """
        return DictField.to_json(obj)

    def to_internal_value(self, data):
        """
        from json format
        """
        return DictField.from_json(data)


class NotificationTypeSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    DRF Serializer definition for NotificationType
    """

    name = serializers.CharField(max_length=255)
    renderer = serializers.CharField(max_length=255)


class NotificationMessageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    DRF Serializer definition for NotificationMessage
    """

    id = serializers.IntegerField()
    msg_type = NotificationTypeSerializer()
    namespace = serializers.CharField(max_length=128, required=False)
    from_user_id = serializers.IntegerField(required=False, allow_null=True)
    payload = DictFieldSerializer()
    deliver_no_earlier_than = serializers.DateTimeField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    expires_secs_after_read = serializers.IntegerField(required=False, allow_null=True)
    created = serializers.DateTimeField()


class UserNotificationSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    DRF Serializer definition for UserNotification
    """

    user_id = serializers.IntegerField()
    msg = NotificationMessageSerializer()
    read_at = serializers.DateTimeField()
    user_context = DictFieldSerializer()
