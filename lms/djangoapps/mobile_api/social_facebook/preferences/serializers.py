"""
Serializer for Share Settings API
"""
from rest_framework import serializers


class UserSharingSerializar(serializers.Serializer):
    """
    Serializes user social settings
    """
    share_with_facebook_friends = serializers.BooleanField(required=True)
