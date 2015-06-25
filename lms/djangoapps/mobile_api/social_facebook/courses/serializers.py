"""
Serializer for courses API
"""
from rest_framework import serializers


class CoursesWithFriendsSerializer(serializers.Serializer):
    """
    Serializes oauth token for facebook groups request
    """
    oauth_token = serializers.CharField(required=True)
