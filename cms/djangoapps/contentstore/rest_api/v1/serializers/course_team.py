"""
API Serializers for course team
"""

from rest_framework import serializers


class UserCourseTeamSerializer(serializers.Serializer):
    """Serializer for user in course team"""
    email = serializers.CharField()
    id = serializers.IntegerField()
    role = serializers.CharField()
    username = serializers.CharField()


class CourseTeamSerializer(serializers.Serializer):
    """Serializer for course team context data"""
    show_transfer_ownership_hint = serializers.BooleanField()
    users = UserCourseTeamSerializer(many=True)
    allow_actions = serializers.BooleanField()
