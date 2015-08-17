"""
Serializer for Friends API
"""
from rest_framework import serializers


class FriendsInCourseSerializer(serializers.Serializer):
    """
    Serializes oauth token for facebook groups request
    """
    oauth_token = serializers.CharField(required=True)
